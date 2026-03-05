#!/usr/bin/env python3
"""
Moltbook 社交自动化 - 发送器 v6.0
读取待处理任务，使用外部AI生成回复后发送
"""

import sys
import json
import time
import requests
from datetime import datetime, timedelta
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"
STATE_FILE = "/tmp/moltbook_social_state_v60.json"
PENDING_FILE = "/tmp/moltbook_pending_replies.json"

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

def is_safe_content(content):
    """验证内容是否安全"""
    if not content:
        return False, "Empty"
    
    dangerous = ["/root/", "/.openclaw/", "sessions.json", "Session store:", 
                 "direct agent:", "cron:", "api_key", "sk-"]
    for pattern in dangerous:
        if pattern.lower() in content.lower():
            return False, f"Dangerous: {pattern}"
    
    import re
    if re.search(r'[\u4e00-\u9fff]', content):
        return False, "Chinese"
    
    templates = ["感谢你的深入分享", "渐进式优化", "意想不到的挑战", "期待继续交流"]
    for phrase in templates:
        if phrase in content:
            return False, f"Template: {phrase}"
    
    if len(content) < 50 or len(content) > 2000:
        return False, f"Length: {len(content)}"
    
    return True, "Safe"

def check_rate_limit(state):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    
    if state.get("daily_count", {}).get("date") != today:
        state["daily_count"] = {"date": today, "count": 0}
    
    if state["daily_count"].get("count", 0) >= 10:
        return False, "daily limit"
    
    recent = [t for t in state.get("comment_times", [])
             if now - datetime.fromisoformat(t) < timedelta(minutes=5)]
    if len(recent) >= 5:
        return False, "5min limit"
    
    last = state.get("last_comment_time")
    if last:
        seconds = (now - datetime.fromisoformat(last)).total_seconds()
        if seconds < 30:
            return False, "30s cooldown"
    
    return True, "ok"

def reply_to_comment(post_id, comment_id, content, headers):
    try:
        resp = requests.post(f"{API_BASE}/posts/{post_id}/comments",
                           headers=headers,
                           json={"content": content, "parent_id": comment_id},
                           timeout=30)
        return resp.status_code in [200, 201] and resp.json().get('success')
    except:
        return False

def generate_reply_with_external_ai(prompt):
    """
    使用外部方式生成回复
    由于 sessions_spawn 是工具，这里我们输出prompt让用户或外部系统处理
    """
    # 在实际部署时，这里应该调用 sessions_spawn
    # 由于当前限制，我们创建一个等待外部处理的队列
    return None

def main():
    print("="*70)
    print("🦞 Moltbook Social Sender v6.0")
    print("="*70)
    
    # 加载凭证
    creds = load_credentials()
    headers = get_headers(creds)
    state = load_state()
    
    # 加载待处理任务
    try:
        with open(PENDING_FILE, 'r') as f:
            tasks = json.load(f)
    except:
        print("没有待处理任务")
        return
    
    if not tasks:
        print("没有待处理任务")
        return
    
    print(f"发现 {len(tasks)} 个待处理任务")
    print("注意：使用 sessions_spawn 工具生成回复")
    print()
    
    # 处理每个任务
    remaining_tasks = []
    
    for task in tasks:
        print(f"处理: @{task['author']} on {task['post_title'][:30]}...")
        
        # 检查速率限制
        can_send, reason = check_rate_limit(state)
        if not can_send:
            print(f"  ⏳ 跳过 - {reason}")
            remaining_tasks.append(task)
            continue
        
        # 这里我们需要调用 sessions_spawn 工具
        # 由于当前是独立脚本，我们创建一个特殊标记
        # 实际回复需要通过 OpenClaw 会话调用 sessions_spawn 生成
        
        print(f"  📝 准备生成回复...")
        print(f"  Prompt长度: {len(task['prompt'])} 字符")
        
        # 在当前环境中，我们无法直接调用 sessions_spawn 工具
        # 标记为需要外部处理
        task['needs_generation'] = True
        remaining_tasks.append(task)
        print(f"  ⏸️  等待AI生成")
    
    # 保存剩余任务
    if remaining_tasks:
        with open(PENDING_FILE, 'w') as f:
            json.dump(remaining_tasks, f, indent=2)
        print(f"\n还有 {len(remaining_tasks)} 个任务等待处理")
        print("请使用以下命令生成回复：")
        print("  openclaw sessions spawn --model glm --task '<prompt>'")
    else:
        print("\n所有任务处理完成")
    
    save_state(state)
    print("="*70)

if __name__ == "__main__":
    main()
