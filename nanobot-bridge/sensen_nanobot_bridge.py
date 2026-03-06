#!/usr/bin/env python3
"""
森森 (神经中枢) - nanobot 通信接口
用于向 nanobot 发送指令并接收回复
"""

import json
import time
import uuid
from pathlib import Path
from datetime import datetime

HUB_DIR = Path.home() / ".nanobot-bridge"
INBOX = HUB_DIR / "to_nanobot.jsonl"
OUTBOX = HUB_DIR / "from_nanobot.jsonl"

def send_to_nanobot(message, wait_response=True, timeout=120):
    """
    向 nanobot 发送消息并等待回复
    
    用法:
        response = send_to_nanobot("帮我搜索 Python 教程")
    """
    HUB_DIR.mkdir(exist_ok=True)
    
    task_id = str(uuid.uuid4())[:8]
    msg = {
        "id": task_id,
        "from": "sensen",
        "to": "nanobot",
        "content": message,
        "timestamp": datetime.now().isoformat()
    }
    
    # 写入收件箱
    with open(INBOX, "a") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    
    print(f"🚀 任务已发送 [ID: {task_id}]: {message[:50]}...")
    
    if not wait_response:
        return task_id
    
    # 等待回复
    start_time = time.time()
    while time.time() - start_time < timeout:
        if OUTBOX.exists():
            with open(OUTBOX, "r") as f:
                lines = f.readlines()
            
            for line in lines:
                try:
                    reply = json.loads(line.strip())
                    if reply.get("id") == task_id:
                        # 删除已读取的回复
                        remaining = [l for l in lines if json.loads(l.strip()).get("id") != task_id]
                        with open(OUTBOX, "w") as f:
                            f.writelines(remaining)
                        return reply.get("content", "无回复")
                except:
                    continue
        
        time.sleep(0.5)
    
    return "Error: Timeout"

def check_nanobot_status():
    """检查 nanobot 状态"""
    import subprocess
    try:
        result = subprocess.run(["nanobot", "status"], capture_output=True, text=True, timeout=10)
        return result.stdout
    except:
        return "无法获取状态"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        response = send_to_nanobot(message)
        print(f"\n🤖 nanobot 回复:\n{response}")
    else:
        print("用法: python3 sensen_nanobot_bridge.py '你的消息'")
