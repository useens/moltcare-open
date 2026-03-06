#!/usr/bin/env python3
"""
森森 ↔ nanobot 实时通信桥接器
Neural Hub (Sensen) - Sub-Agent (nanobot) Bridge
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# 配置
HUB_DIR = Path.home() / ".nanobot-bridge"
INBOX = HUB_DIR / "to_nanobot.jsonl"
OUTBOX = HUB_DIR / "from_nanobot.jsonl"
LOG_FILE = HUB_DIR / "bridge.log"
NANOBOT_BIN = "/usr/local/bin/nanobot"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def ensure_files():
    """确保通信文件存在"""
    HUB_DIR.mkdir(exist_ok=True)
    for f in [INBOX, OUTBOX]:
        if not f.exists():
            f.touch()

def read_messages(filepath):
    """读取消息队列"""
    messages = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return messages

def write_message(filepath, msg_dict):
    """写入消息"""
    with open(filepath, "a") as f:
        f.write(json.dumps(msg_dict, ensure_ascii=False) + "\n")

def clear_messages(filepath):
    """清空消息队列"""
    open(filepath, "w").close()

def call_nanobot(message, task_id):
    """调用 nanobot 处理消息"""
    try:
        result = subprocess.run(
            [NANOBOT_BIN, "agent", "-m", message],
            capture_output=True,
            text=True,
            timeout=120
        )
        response = result.stdout.strip()
        if result.returncode != 0:
            response = f"Error: {result.stderr}"
        return response
    except subprocess.TimeoutExpired:
        return "Error: Timeout"
    except Exception as e:
        return f"Error: {str(e)}"

def process_tasks():
    """处理来自神经中枢的任务"""
    ensure_files()
    
    messages = read_messages(INBOX)
    if not messages:
        return
    
    log(f"收到 {len(messages)} 个任务")
    
    for msg in messages:
        task_id = msg.get("id", "unknown")
        content = msg.get("content", "")
        from_hub = msg.get("from", "unknown")
        
        log(f"处理任务 {task_id}: {content[:50]}...")
        
        # 调用 nanobot
        response = call_nanobot(content, task_id)
        
        # 发送回复
        reply = {
            "id": task_id,
            "from": "nanobot",
            "to": from_hub,
            "content": response,
            "timestamp": datetime.now().isoformat()
        }
        write_message(OUTBOX, reply)
        log(f"任务 {task_id} 完成")
    
    # 清空收件箱
    clear_messages(INBOX)

def main():
    """主循环 - nanobot 小弟模式"""
    log("=" * 50)
    log("nanobot 小弟模式启动")
    log("等待神经中枢 (森森) 的指令...")
    log(f"收件箱: {INBOX}")
    log(f"发件箱: {OUTBOX}")
    log("=" * 50)
    
    ensure_files()
    
    while True:
        try:
            process_tasks()
            time.sleep(1)  # 每秒检查一次
        except KeyboardInterrupt:
            log("收到中断信号，退出...")
            break
        except Exception as e:
            log(f"错误: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
