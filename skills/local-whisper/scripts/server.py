#!/usr/bin/env python3
"""
Whisper Server - 常驻内存模型服务
模型常驻内存，通过socket提供转录服务
"""

import os
import sys
import json
import socket
import signal
import tempfile
from pathlib import Path

# 配置
SOCK_FILE = "/tmp/whisper_server.sock"
PID_FILE = "/tmp/whisper_server.pid"
DEFAULT_MODEL = "base"

# 全局状态
_model = None
_model_name = None

def log(msg):
    print(f"[WhisperServer] {msg}", file=sys.stderr, flush=True)

def load_model(model_name):
    """加载模型到内存（只执行一次）"""
    global _model, _model_name
    if _model is None:
        import whisper
        log(f"Loading model: {model_name}")
        _model = whisper.load_model(model_name)
        _model_name = model_name
        log(f"Model ready: {model_name}")
    return _model

def transcribe(audio_path, language=None):
    """转录音频"""
    try:
        model = load_model(DEFAULT_MODEL)
        result = model.transcribe(audio_path, language=language, verbose=False)
        return {
            "success": True,
            "text": result.get("text", "").strip(),
            "language": result.get("language", "unknown")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_client(conn):
    """处理客户端请求"""
    try:
        data = conn.recv(4096).decode()
        req = json.loads(data)
        
        cmd = req.get("cmd")
        if cmd == "transcribe":
            audio = req.get("audio")
            lang = req.get("language")
            if not audio or not Path(audio).exists():
                resp = {"success": False, "error": "Audio file not found"}
            else:
                resp = transcribe(audio, lang)
        elif cmd == "ping":
            resp = {"success": True, "status": "alive", "model": DEFAULT_MODEL}
        else:
            resp = {"success": False, "error": "Unknown command"}
        
        conn.send(json.dumps(resp).encode())
    except Exception as e:
        conn.send(json.dumps({"success": False, "error": str(e)}).encode())
    finally:
        conn.close()

def start_server():
    """启动服务器"""
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
    
    # 创建socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(SOCK_FILE)
    s.listen(5)
    
    log(f"Ready on {SOCK_FILE}")
    
    def shutdown(signum, frame):
        log("Shutting down...")
        s.close()
        Path(PID_FILE).unlink(missing_ok=True)
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    
    try:
        while True:
            conn, _ = s.accept()
            handle_client(conn)
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    start_server()
