#!/usr/bin/env python3
"""
Whisper Transcription Server (Daemon Mode)
Keeps model loaded in memory for fast transcription
"""

import os
import sys
import json
import socket
import threading
import time
from pathlib import Path

# Configuration
SOCKET_PATH = "/tmp/whisper_daemon.sock"
PID_FILE = "/tmp/whisper_daemon.pid"
DEFAULT_MODEL = "base"

# Global state
_model = None
_model_name = None


def load_model(model_name):
    """Load Whisper model."""
    global _model, _model_name
    
    if _model is None or _model_name != model_name:
        import whisper
        print(f"[Daemon] Loading model: {model_name}", file=sys.stderr)
        _model = whisper.load_model(model_name)
        _model_name = model_name
        print(f"[Daemon] Model loaded: {model_name}", file=sys.stderr)
    return _model


def transcribe(audio_file, model_name, language=None):
    """Transcribe audio using loaded model."""
    model = load_model(model_name)
    
    result = model.transcribe(audio_file, language=language, verbose=False)
    return {
        "text": result.get("text", "").strip(),
        "language": result.get("language", "unknown")
    }


def handle_client(conn):
    """Handle client request."""
    try:
        data = conn.recv(4096).decode()
        request = json.loads(data)
        
        audio_file = request.get("audio_file")
        model = request.get("model", DEFAULT_MODEL)
        language = request.get("language")
        
        if not audio_file or not Path(audio_file).exists():
            response = {"error": "Audio file not found"}
        else:
            start = time.time()
            result = transcribe(audio_file, model, language)
            result["processing_time"] = round(time.time() - start, 2)
            result["model_cached"] = True
            response = result
        
        conn.send(json.dumps(response).encode())
    except Exception as e:
        conn.send(json.dumps({"error": str(e)}).encode())
    finally:
        conn.close()


def start_daemon():
    """Start the transcription daemon."""
    # Check if already running
    if Path(PID_FILE).exists():
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Check if process exists
            print(f"[Daemon] Already running (PID {pid})", file=sys.stderr)
            return
        except (OSError, ValueError):
            pass
    
    # Remove old socket
    if Path(SOCKET_PATH).exists():
        os.remove(SOCKET_PATH)
    
    # Write PID file
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    
    # Preload default model
    print("[Daemon] Starting Whisper daemon...", file=sys.stderr)
    load_model(DEFAULT_MODEL)
    
    # Create socket
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(5)
    
    print(f"[Daemon] Ready on {SOCKET_PATH}", file=sys.stderr)
    
    try:
        while True:
            conn, _ = server.accept()
            threading.Thread(target=handle_client, args=(conn,)).start()
    except KeyboardInterrupt:
        print("[Daemon] Shutting down...", file=sys.stderr)
    finally:
        server.close()
        Path(PID_FILE).unlink(missing_ok=True)


def client_request(audio_file, model, language):
    """Send request to daemon."""
    if not Path(SOCKET_PATH).exists():
        print("Error: Daemon not running. Start with: python daemon.py --start", file=sys.stderr)
        sys.exit(1)
    
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        
        request = {
            "audio_file": audio_file,
            "model": model,
            "language": language
        }
        client.send(json.dumps(request).encode())
        
        response = client.recv(4096).decode()
        client.close()
        
        return json.loads(response)
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Whisper Transcription Daemon")
    parser.add_argument("--start", action="store_true", help="Start daemon")
    parser.add_argument("--stop", action="store_true", help="Stop daemon")
    parser.add_argument("--status", action="store_true", help="Check status")
    parser.add_argument("--transcribe", help="Transcribe audio file")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model size")
    parser.add_argument("--language", help="Language code")
    
    args = parser.parse_args()
    
    if args.start:
        start_daemon()
    elif args.stop:
        if Path(PID_FILE).exists():
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 15)
            print(f"[Daemon] Stopped (PID {pid})")
        else:
            print("[Daemon] Not running")
    elif args.status:
        if Path(PID_FILE).exists() and Path(SOCKET_PATH).exists():
            print("[Daemon] Running")
        else:
            print("[Daemon] Not running")
    elif args.transcribe:
        result = client_request(args.transcribe, args.model, args.language)
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(result["text"])
    else:
        parser.print_help()
