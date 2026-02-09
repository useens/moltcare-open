#!/usr/bin/env python3
"""
Whisper Client v2.0 - 支持同步/异步模式
"""

import os
import sys
import json
import socket
import time
import subprocess
import signal
from pathlib import Path

SOCK_FILE = "/tmp/whisper_server.sock"
PID_FILE = "/tmp/whisper_server.pid"
SERVER_SCRIPT = Path(__file__).parent / "server_v2.py"
VENV_PYTHON = Path(__file__).parent.parent / ".venv/bin/python"

def send_request(req, timeout=30):
    """发送请求到服务器"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(SOCK_FILE)
        s.send(json.dumps(req).encode())
        resp = json.loads(s.recv(8192).decode())
        s.close()
        return resp
    except Exception as e:
        return {"success": False, "error": str(e)}

def ensure_server():
    """确保服务器在运行"""
    # 检查服务器是否响应
    resp = send_request({"cmd": "ping"}, timeout=2)
    if resp.get("success"):
        return True
    
    # 启动服务器
    print("[Client] Starting server...", file=sys.stderr)
    subprocess.Popen(
        [str(VENV_PYTHON), str(SERVER_SCRIPT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # 等待服务器就绪
    for i in range(30):
        time.sleep(0.3)
        resp = send_request({"cmd": "ping"}, timeout=1)
        if resp.get("success"):
            print("[Client] Server ready", file=sys.stderr)
            return True
    
    return False

def transcribe_sync(audio_path, language=None):
    """同步转录（阻塞等待结果）"""
    if not ensure_server():
        return {"success": False, "error": "Failed to start server"}
    
    return send_request({
        "cmd": "transcribe",
        "audio": str(audio_path),
        "language": language,
        "sync": True
    })

def transcribe_async(audio_path, language=None):
    """异步转录（返回task_id，非阻塞）"""
    if not ensure_server():
        return {"success": False, "error": "Failed to start server"}
    
    return send_request({
        "cmd": "transcribe",
        "audio": str(audio_path),
        "language": language,
        "sync": False
    })

def query_task(task_id, timeout=60):
    """查询异步任务结果"""
    start = time.time()
    while time.time() - start < timeout:
        resp = send_request({"cmd": "query", "task_id": task_id}, timeout=5)
        if resp.get("status") in ["completed", "failed"]:
            return resp
        time.sleep(0.5)
    return {"success": False, "error": "Timeout waiting for result"}

def get_stats():
    """获取服务器统计信息"""
    return send_request({"cmd": "stats"})

def stop_server():
    """停止服务器"""
    if Path(PID_FILE).exists():
        with open(PID_FILE) as f:
            pid = int(f.read())
        try:
            os.kill(pid, signal.SIGTERM)
            print("[Client] Server stopped")
            return True
        except:
            return False
    return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Whisper Client v2.0")
    parser.add_argument("audio", nargs="?", help="Audio file path")
    parser.add_argument("-l", "--language", default="zh", help="Language code")
    parser.add_argument("--async", dest="async_mode", action="store_true", help="Async mode")
    parser.add_argument("--query", help="Query async task result")
    parser.add_argument("--stats", action="store_true", help="Show server stats")
    parser.add_argument("--stop", action="store_true", help="Stop server")
    parser.add_argument("--wait", type=int, default=30, help="Max wait time for async")
    args = parser.parse_args()
    
    if args.stop:
        stop_server()
        sys.exit(0)
    
    if args.stats:
        result = get_stats()
        if result.get("success"):
            stats = result.get("stats", {})
            print(f"Server Statistics:")
            print(f"  Total tasks: {stats.get('total_tasks', 0)}")
            print(f"  Completed: {stats.get('completed_tasks', 0)}")
            print(f"  Failed: {stats.get('failed_tasks', 0)}")
            print(f"  Queue size: {result.get('queue_size', 0)}")
            print(f"  Cached results: {result.get('cached_results', 0)}")
        else:
            print(f"Error: {result.get('error')}")
        sys.exit(0)
    
    if args.query:
        result = query_task(args.query, args.wait)
        if result.get("status") == "completed":
            print(result.get("text", ""))
        elif result.get("status") == "failed":
            print(f"Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Task still pending (queue: {result.get('queue_size', 0)})")
        sys.exit(0)
    
    if not args.audio:
        parser.print_help()
        sys.exit(1)
    
    if args.async_mode:
        # 异步模式
        result = transcribe_async(args.audio, args.language)
        if result.get("success"):
            print(f"Task queued: {result.get('task_id')}")
            print(f"Queue position: {result.get('queue_position', 0)}")
        else:
            print(f"Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)
    else:
        # 同步模式
        result = transcribe_sync(args.audio, args.language)
        if result.get("success"):
            print(result.get("text", ""))
        else:
            print(f"Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)
