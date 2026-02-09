#!/usr/bin/env python3
"""
Whisper Client - 连接常驻服务器
"""

import os
import sys
import json
import socket
import time
import subprocess
from pathlib import Path

SOCK_FILE = "/tmp/whisper_server.sock"
PID_FILE = "/tmp/whisper_server.pid"
SERVER_SCRIPT = Path(__file__).parent / "server.py"
VENV_PYTHON = Path(__file__).parent.parent / ".venv/bin/python"

def ensure_server():
    """确保服务器在运行"""
    # 检查socket是否存在且服务器响应
    if Path(SOCK_FILE).exists():
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect(SOCK_FILE)
            s.send(json.dumps({"cmd": "ping"}).encode())
            resp = json.loads(s.recv(1024).decode())
            s.close()
            if resp.get("success"):
                return True
        except:
            pass
    
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
        time.sleep(0.5)
        if Path(SOCK_FILE).exists():
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect(SOCK_FILE)
                s.send(json.dumps({"cmd": "ping"}).encode())
                resp = json.loads(s.recv(1024).decode())
                s.close()
                if resp.get("success"):
                    print("[Client] Server ready", file=sys.stderr)
                    return True
            except:
                pass
    
    return False

def transcribe(audio_path, language=None):
    """转录音频"""
    if not ensure_server():
        print("Error: Failed to start server", file=sys.stderr)
        sys.exit(1)
    
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(30)
        s.connect(SOCK_FILE)
        
        req = {
            "cmd": "transcribe",
            "audio": str(audio_path),
            "language": language
        }
        s.send(json.dumps(req).encode())
        
        resp = json.loads(s.recv(8192).decode())
        s.close()
        
        return resp
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", help="Audio file path")
    parser.add_argument("-l", "--language", help="Language code")
    parser.add_argument("--stop", action="store_true", help="Stop server")
    args = parser.parse_args()
    
    if args.stop:
        if Path(PID_FILE).exists():
            with open(PID_FILE) as f:
                pid = int(f.read())
            os.kill(pid, signal.SIGTERM)
            print("Server stopped")
        sys.exit(0)
    
    result = transcribe(args.audio, args.language)
    
    if result.get("success"):
        print(result["text"])
    else:
        print(f"Error: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
