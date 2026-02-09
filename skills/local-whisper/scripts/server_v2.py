#!/usr/bin/env python3
"""
Whisper Server v2.0 - 队列管理 + 异步处理
模型常驻内存，支持并发队列和后台异步转录
"""

import os
import sys
import json
import socket
import signal
import threading
import queue
import time
import uuid
from pathlib import Path
from collections import OrderedDict

# 配置
SOCK_FILE = "/tmp/whisper_server.sock"
PID_FILE = "/tmp/whisper_server.pid"
DEFAULT_MODEL = "base"
MAX_QUEUE_SIZE = 100
WORKER_THREADS = 2  # 并发工作线程数
RESULT_TTL = 300    # 结果缓存5分钟

def log(msg):
    print(f"[WhisperServer] {msg}", file=sys.stderr, flush=True)

# ============ 全局状态 ============
_model = None
_model_lock = threading.Lock()
_task_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
_results = OrderedDict()  # 任务结果缓存
_results_lock = threading.Lock()
_workers = []
_shutdown_event = threading.Event()
_stats = {
    "total_tasks": 0,
    "completed_tasks": 0,
    "failed_tasks": 0,
    "queue_high_water": 0
}
_stats_lock = threading.Lock()

# ============ 模型管理 ============
def load_model(model_name):
    """线程安全加载模型"""
    global _model
    with _model_lock:
        if _model is None:
            import whisper
            log(f"Loading model: {model_name}")
            _model = whisper.load_model(model_name)
            log(f"Model ready")
        return _model

# ============ 任务处理 ============
def process_task(task_id, audio_path, language):
    """执行转录任务"""
    try:
        model = load_model(DEFAULT_MODEL)
        result = model.transcribe(str(audio_path), language=language, verbose=False)
        
        with _results_lock:
            _results[task_id] = {
                "status": "completed",
                "text": result.get("text", "").strip(),
                "language": result.get("language", "unknown"),
                "completed_at": time.time()
            }
        
        with _stats_lock:
            _stats["completed_tasks"] += 1
            
    except Exception as e:
        with _results_lock:
            _results[task_id] = {
                "status": "failed",
                "error": str(e),
                "completed_at": time.time()
            }
        with _stats_lock:
            _stats["failed_tasks"] += 1

def worker_loop():
    """工作线程主循环"""
    while not _shutdown_event.is_set():
        try:
            task = _task_queue.get(timeout=1)
            if task is None:  # 停止信号
                break
            
            task_id, audio_path, language = task
            log(f"Processing task {task_id[:8]}...")
            process_task(task_id, audio_path, language)
            _task_queue.task_done()
            
        except queue.Empty:
            continue
        except Exception as e:
            log(f"Worker error: {e}")

# ============ 结果清理 ============
def cleanup_results():
    """定期清理过期结果"""
    while not _shutdown_event.is_set():
        time.sleep(60)
        now = time.time()
        with _results_lock:
            expired = [k for k, v in _results.items() 
                      if now - v.get("completed_at", 0) > RESULT_TTL]
            for k in expired:
                del _results[k]
            if expired:
                log(f"Cleaned up {len(expired)} expired results")

# ============ 网络处理 ============
def handle_client(conn):
    """处理客户端请求"""
    try:
        conn.settimeout(30)
        data = conn.recv(4096).decode()
        req = json.loads(data)
        
        cmd = req.get("cmd")
        
        # 同步转录（等待结果）
        if cmd == "transcribe":
            audio = req.get("audio")
            lang = req.get("language")
            sync = req.get("sync", True)  # 默认同步模式
            
            if not audio or not Path(audio).exists():
                resp = {"success": False, "error": "Audio file not found"}
            else:
                if sync:
                    # 同步模式：直接处理
                    task_id = str(uuid.uuid4())[:12]
                    log(f"Sync task {task_id[:8]}: {Path(audio).name}")
                    process_task(task_id, audio, lang)
                    result = _results.get(task_id, {})
                    resp = {
                        "success": result.get("status") == "completed",
                        "text": result.get("text", ""),
                        "language": result.get("language", "unknown"),
                        "task_id": task_id
                    }
                else:
                    # 异步模式：加入队列
                    if _task_queue.qsize() >= MAX_QUEUE_SIZE:
                        resp = {"success": False, "error": "Queue full"}
                    else:
                        task_id = str(uuid.uuid4())[:12]
                        _task_queue.put((task_id, audio, lang))
                        
                        with _stats_lock:
                            _stats["total_tasks"] += 1
                            current_qsize = _task_queue.qsize()
                            if current_qsize > _stats["queue_high_water"]:
                                _stats["queue_high_water"] = current_qsize
                        
                        resp = {
                            "success": True,
                            "task_id": task_id,
                            "status": "queued",
                            "queue_position": _task_queue.qsize()
                        }
        
        # 查询异步任务结果
        elif cmd == "query":
            task_id = req.get("task_id")
            with _results_lock:
                result = _results.get(task_id, {"status": "not_found"})
            
            if result["status"] == "completed":
                resp = {
                    "success": True,
                    "status": "completed",
                    "text": result.get("text", ""),
                    "language": result.get("language", "unknown")
                }
            elif result["status"] == "failed":
                resp = {
                    "success": False,
                    "status": "failed",
                    "error": result.get("error", "Unknown error")
                }
            else:
                # 还在队列中
                resp = {
                    "success": True,
                    "status": "pending",
                    "queue_size": _task_queue.qsize()
                }
        
        # 获取统计信息
        elif cmd == "stats":
            with _stats_lock:
                resp = {
                    "success": True,
                    "stats": _stats.copy(),
                    "queue_size": _task_queue.qsize(),
                    "cached_results": len(_results)
                }
        
        # 健康检查
        elif cmd == "ping":
            resp = {
                "success": True,
                "status": "alive",
                "model": DEFAULT_MODEL,
                "workers": len(_workers),
                "queue_size": _task_queue.qsize()
            }
        
        else:
            resp = {"success": False, "error": "Unknown command"}
        
        conn.send(json.dumps(resp).encode())
        
    except socket.timeout:
        log("Client timeout")
    except Exception as e:
        log(f"Client error: {e}")
        try:
            conn.send(json.dumps({"success": False, "error": str(e)}).encode())
        except:
            pass
    finally:
        conn.close()

# ============ 服务器主循环 ============
def start_workers():
    """启动工作线程"""
    global _workers
    for i in range(WORKER_THREADS):
        t = threading.Thread(target=worker_loop, daemon=True)
        t.start()
        _workers.append(t)
    log(f"Started {WORKER_THREADS} worker threads")

def start_server():
    """启动服务器"""
    global _workers
    
    # 检查是否已在运行
    if Path(PID_FILE).exists():
        try:
            with open(PID_FILE) as f:
                pid = int(f.read())
            os.kill(pid, 0)
            log(f"Already running (PID {pid})")
            return
        except:
            pass
    
    # 清理旧文件
    for f in [SOCK_FILE, PID_FILE]:
        Path(f).unlink(missing_ok=True)
    
    # 写PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    
    # 预加载模型
    log("Preloading model...")
    load_model(DEFAULT_MODEL)
    
    # 启动工作线程
    start_workers()
    
    # 启动结果清理线程
    cleanup_thread = threading.Thread(target=cleanup_results, daemon=True)
    cleanup_thread.start()
    
    # 创建socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(SOCK_FILE)
    s.listen(10)
    os.chmod(SOCK_FILE, 0o666)  # 允许所有用户访问
    
    log(f"Ready on {SOCK_FILE} ({WORKER_THREADS} workers)")
    
    def shutdown(signum, frame):
        log("Shutting down...")
        _shutdown_event.set()
        
        # 停止工作线程
        for _ in _workers:
            _task_queue.put(None)
        for w in _workers:
            w.join(timeout=2)
        
        s.close()
        Path(PID_FILE).unlink(missing_ok=True)
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    
    try:
        while not _shutdown_event.is_set():
            try:
                s.settimeout(1)
                conn, _ = s.accept()
                threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    start_server()
