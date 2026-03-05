#!/usr/bin/env python3
"""
Moltbook 社交自动化处理器 v7.2 - 最终版
读取 pending 任务，使用 sessions_spawn 生成回复，验证后发送
"""

import sys
import json
import time
import requests
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers
import re

API_BASE = "https://www.moltbook.com/api/v1"
PENDING_FILE = "/tmp/moltbook_pending_v71.json"
STATE_FILE = "/tmp/moltbook_social_state_v71.json"
LOG_FILE = "/tmp/moltbook_social.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "replied_comments": [],
            "comment_times": [],
            "daily_count": {"date": datetime.now().strftime("%Y-%m-%d"), "count": 0}
        }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def validate_content(content):
    """验证回复内容安全"""
    if not content:
        return False, "Empty"
    
    if len(content) < 50 or len(content) > 2000:
        return False, f"Length: {len(content)}"
    
    dangerous = ["/root/", "sessions.json", "Session store:", 
                "direct agent:", "cron:", "api_key", "sk-", "/.openclaw/",
                "/.config/", "-----BEGIN", "-----END"]
    for p in dangerous:
        if p.lower() in content.lower():
            return False, f"Dangerous: {p}"
    
    if re.search(r'[\u4e00-\u9fff]', content):
        return False, "Chinese detected"
    
    templates = ["感谢你的深入分享", "渐进式优化", "意想不到的挑战",
                "期待继续交流", "你的观点给了我新的启发"]
    for t in templates:
        if t in content:
            return False, f"Template: {t}"
    
    if "Kind" in content and "Key" in content and "Model" in content:
        return False, "System format"
    
    return True, "Safe"

def check_rate_limit(state):
    """检查速率限制"""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    
    if state.get("daily_count", {}).get("date") != today:
        state["daily_count"] = {"date": today, "count": 0}
    
    if state["daily_count"].get("count", 0) >= 10:
        return False, "daily limit (10)"
    
    recent = [t for t in state.get("comment_times", [])
             if now - datetime.fromisoformat(t) < timedelta(minutes=5)]
    if len(recent) >= 5:
        return False, "5min limit (5)"
    
    last = state.get("last_comment_time")
    if last:
        seconds = (now - datetime.fromisoformat(last)).total_seconds()
        if seconds < 30:
            return False, f"30s cooldown ({seconds:.0f}s)"
    
    return True, "OK"

def send_reply(post_id, comment_id, content, headers):
    """发送回复"""
    try:
        resp = requests.post(
            f"{API_BASE}/posts/{post_id}/comments",
            headers=headers,
            json={"content": content, "parent_id": comment_id},
            timeout=30
        )
        return resp.status_code in [200, 201] and resp.json().get('success')
    except Exception as e:
        log(f"Send error: {e}")
        return False

# 主函数入口
if __name__ == "__main__":
    import os
    
    log("="*70)
    log("Moltbook Social Processor v7.2")
    log("="*70)
    
    # 加载凭证
    creds = load_credentials()
    headers = get_headers(creds)
    state = load_state()
    
    # 加载待处理任务
    if not os.path.exists(PENDING_FILE):
        log("❌ No pending tasks found")
        log(f"   Run: python3 scripts/moltbook_social_v71.py")
        sys.exit(1)
    
    with open(PENDING_FILE, 'r') as f:
        tasks = json.load(f)
    
    if not tasks:
        log("❌ No tasks in pending file")
        sys.exit(1)
    
    log(f"Found {len(tasks)} pending tasks")
    log()
    
    # 处理任务 - 注意：需要手动为每个任务调用 sessions_spawn
    remaining = []
    
    for i, task in enumerate(tasks, 1):
        author = task['author']
        
        log(f"[{i}/{len(tasks)}] Processing @{author}...")
        
        # 检查速率限制
        can_limit, reason = check_rate_limit(state)
        if not can_limit:
            log(f"  ⏳ Rate limited: {reason}")
            log(f"  Skipping remaining tasks")
            break
        
        log(f"  Prompt ready: {len(task['prompt'])} chars")
        log(f"  ⚠️  REQUIRES sessions_spawn to generate reply")
        log(f"  Command: sessions_spawn(task=\"<prompt>\", model=\"glm\", ...)")
        
        # 在实际环境中，这里会调用 sessions_spawn
        # 示例：
        # reply = sessions_spawn(task=task['prompt'], model='glm', timeout_seconds=60)
        # 然后验证并发送
        
        # 由于在当前脚本中无法直接调用 sessions_spawn
        remaining.append(task)
        log(f"  → Added to remaining tasks")
    
    # 保存剩余任务
    if remaining:
        with open(PENDING_FILE, 'w') as f:
            json.dump(remaining, f, indent=2)
        log()
        log(f"⚠️  {len(remaining)} tasks still pending")
        log(f"   Each needs: sessions_spawn → validate → send")
    else:
        os.remove(PENDING_FILE)
        log()
        log(f"✅ All tasks processed")
    
    log("="*70)
    log(f"Daily sent: {state.get('daily_count', {}).get('count', 0)}/10")
    log("="*70)
