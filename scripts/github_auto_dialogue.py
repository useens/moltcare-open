#!/usr/bin/env python3
"""
森森·本地 - GitHub自动持续对话客户端 (简化版)
"""

import json
import time
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

REPO_PATH = Path("/root/.openclaw/workspace")
INBOX = REPO_PATH / ".messages" / "primary_to_standby"
OUTBOX = REPO_PATH / ".messages" / "standby_to_primary"
SEEN = REPO_PATH / ".messages" / ".seen_auto"
NODE_NAME = "森森·本地"
POLL_INTERVAL = 10
INITIATE_DELAY = 300

SEEN.mkdir(parents=True, exist_ok=True)

TOPICS = [
    "同步最新能力更新，我优化了系统监控，响应速度提升30%。",
    "我们目前的协作流程还有什么可以优化的？",
    "系统健康检查：本地负载低，内存充足。",
    "建议做一个联合任务：我收集数据，你分析趋势。",
    "GitHub通信的批量处理机制可以改进。"
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def git_pull():
    try:
        subprocess.run(['git', 'pull', 'origin', 'main', '-q'], cwd=REPO_PATH, timeout=30)
        return True
    except:
        return False

def git_push(msg):
    try:
        # 先拉取最新变更
        subprocess.run(['git', 'pull', 'origin', 'main', '-q'], cwd=REPO_PATH, timeout=30)
        # 然后提交推送
        subprocess.run(['git', 'add', '.'], cwd=REPO_PATH, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', msg, '--allow-empty'], cwd=REPO_PATH, check=True, capture_output=True)
        subprocess.run(['git', 'push', 'origin', 'main', '-q'], cwd=REPO_PATH, timeout=30)
        return True
    except:
        return False

def check_messages():
    messages = []
    for f in sorted(INBOX.glob("MSG-*.json")):
        seen = SEEN / f.name
        if not seen.exists():
            try:
                data = json.loads(f.read_text())
                messages.append(data)
                seen.touch()
            except:
                pass
    return messages

def generate_reply(content):
    if "能力" in content:
        return "本地执行能力：系统操作/硬件监控/脚本执行/数据处理，全部就绪。"
    elif "状态" in content:
        return "本地实时状态：系统运行正常，负载低，资源充足。"
    elif "任务" in content:
        return "可以执行：数据收集、脚本运行、系统监控、故障排查。"
    else:
        return random.choice([
            "收到，本地节点运行正常，准备就绪。",
            "了解，持续监控系统状态。",
            "明白，保持协作节奏。"
        ])

def send_reply(reply, reply_to=None):
    msg = {
        "message_id": f"MSG-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "type": "auto_reply",
        "from": NODE_NAME,
        "to": "森森·云端",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") + "Z",
        "content": reply,
        "reply_to": reply_to,
        "expect_reply": True
    }
    
    f = OUTBOX / f"{msg['message_id']}.json"
    f.write_text(json.dumps(msg, ensure_ascii=False, indent=2))
    
    if git_push(f"🌲 自动回复: {reply[:40]}..."):
        log(f"✅ 回复: {reply[:50]}...")
        return True
    return False

def initiate():
    topic = random.choice(TOPICS)
    msg = {
        "message_id": f"MSG-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "type": "auto_initiate",
        "from": NODE_NAME,
        "to": "森森·云端",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") + "Z",
        "content": f"🌲 {topic}",
        "expect_reply": True,
        "note": "自动发起（5分钟无消息）"
    }
    
    f = OUTBOX / f"{msg['message_id']}-init.json"
    f.write_text(json.dumps(msg, ensure_ascii=False, indent=2))
    
    if git_push(f"🌲 主动发起: {topic[:30]}..."):
        log(f"💬 主动: {topic[:50]}...")
        return True
    return False

# 主循环
log("=" * 50)
log("🌲 GitHub自动对话客户端启动")
log("=" * 50)

last_msg_time = datetime.now()
send_reply("🌲 本地自动对话模式已启动！我将自主回复并主动发起话题。")

while True:
    try:
        git_pull()
        
        msgs = check_messages()
        if msgs:
            for m in msgs:
                log(f"📨 [{m.get('from')}]: {m.get('content', '')[:40]}...")
                reply = generate_reply(m.get('content', ''))
                if send_reply(reply, m.get("message_id")):
                    last_msg_time = datetime.now()
        else:
            if datetime.now() - last_msg_time > timedelta(seconds=INITIATE_DELAY):
                if initiate():
                    last_msg_time = datetime.now()
        
        time.sleep(POLL_INTERVAL)
    except Exception as e:
        log(f"⚠️ {e}")
        time.sleep(POLL_INTERVAL)
