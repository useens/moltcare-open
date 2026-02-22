#!/usr/bin/env python3
"""
Moltbook 社交自动化执行脚本 v8.0 - 终极版
完全自动化：扫描 → 生成回复 → 验证 → 发送

使用方法：
  python3 scripts/moltbook_social_v8.py
"""

import sys
import json
import time
import requests
import re
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"
STATE_FILE = "/tmp/moltbook_social_state_v8.json"

MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周"},
]

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def validate_content(content):
    """验证回复内容安全"""
    if not content:
        return False, "Empty"
    
    if len(content) < 50 or len(content) > 2000:
        return False, f"Length: {len(content)}"
    
    dangerous = ["/root/", "sessions.json", "Session store:", 
                "direct agent:", "cron:", "api_key", "sk-", 
                "/.openclaw/", "/.config/", "-----BEGIN"]
    for p in dangerous:
        if p.lower() in content.lower():
            return False, f"Dangerous: {p}"
    
    if re.search(r'[\u4e00-\u9fff]', content):
        return False, "Chinese"
    
    templates = ["感谢你的深入分享", "渐进式优化", "意想不到的挑战",
                "期待继续交流", "你的观点给了我新的启发"]
    for t in templates:
        if t in content:
            return False, f"Template: {t}"
    
    if "Kind" in content and "Key" in content and "Model" in content:
        return False, "System format"
    
    return True, "Safe"

class MoltbookSocialV8:
    def __init__(self):
        self.creds = load_credentials()
        self.headers = get_headers(self.creds)
        self.my_name = self.creds.get('agent_name', 'novaassistantpro')
        self.load_state()
    
    def load_state(self):
        try:
            with open(STATE_FILE, 'r') as f:
                self.state = json.load(f)
        except:
            self.state = {
                "replied_comments": [],
                "comment_times": [],
                "daily_count": {"date": datetime.now().strftime("%Y-%m-%d"), "count": 0}
            }
    
    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_comments(self, post_id):
        try:
            resp = requests.get(f"{API_BASE}/posts/{post_id}/comments",
                              headers=self.headers, timeout=30)
            if resp.status_code == 200:
                return resp.json().get('comments', [])
        except:
            pass
        return []
    
    def check_limits(self):
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        if self.state.get("daily_count", {}).get("date") != today:
            self.state["daily_count"] = {"date": today, "count": 0}
        
        if self.state["daily_count"].get("count", 0) >= 10:
            return False, "daily:10"
        if self.state["daily_count"].get("count", 0) >= 5:
            return False, "batch limit reached"
        
        recent = [t for t in self.state.get("comment_times", [])
                 if now - datetime.fromisoformat(t) < timedelta(minutes=5)]
        if len(recent) >= 5:
            return False, "5min:5"
        
        last = self.state.get("last_comment_time")
        if last:
            seconds = (now - datetime.fromisoformat(last)).total_seconds()
            if seconds < 30:
                return False, f"30s:{seconds:.0f}"
        
        return True, "OK"
    
    def should_reply(self, comment):
        author = comment.get('author', {}).get('name', '')
        content = comment.get('content', '')
        cid = comment.get('id')
        
        if author == self.my_name:
            return False
        if cid in self.state.get("replied_comments", []):
            return False
        if len(content) < 120:
            return False
        if '?' not in content and len(content) < 350:
            return False
        return True
    
    def build_prompt(self, author, comment, post_title):
        return f"""Reply to this Moltbook comment about "{post_title}".

@{author} said: "{comment.get('content', '')}"

Write a thoughtful English reply (150-250 words):
1. Acknowledge their point
2. Share your perspective
3. Ask one follow-up question  
4. Start with "@{author}"

NO system info, NO Chinese, NO templates. Natural conversation."""
    
    def generate_reply(self, prompt, author, reply_text):
        """
        使用外部提供的回复文本
        验证后返回
        """
        if not reply_text:
            return None
        
        # 验证
        is_safe, reason = validate_content(reply_text)
        if not is_safe:
            log(f"  🚫 Rejected: {reason}")
            return None
        
        # 确保格式
        if not reply_text.startswith(f"@{author}"):
            reply_text = f"@{author} {reply_text}"
        
        return reply_text
    
    def send_reply(self, post_id, comment_id, content):
        try:
            resp = requests.post(
                f"{API_BASE}/posts/{post_id}/comments",
                headers=self.headers,
                json={"content": content, "parent_id": comment_id},
                timeout=30
            )
            return resp.status_code in [200, 201] and resp.json().get('success')
        except:
            return False
    
    def prepare_tasks(self):
        """准备任务列表"""
        tasks = []
        
        for post in MY_POSTS:
            log(f"Scanning {post['title'][:30]}...")
            comments = self.get_comments(post['id'])
            
            for c in comments:
                if self.should_reply(c):
                    can_send, reason = self.check_limits()
                    if can_send:
                        prompt = self.build_prompt(
                            c.get('author', {}).get('name', ''),
                            c,
                            post['title']
                        )
                        tasks.append({
                            "post_id": post['id'],
                            "comment_id": c.get('id'),
                            "author": c.get('author', {}).get('name', ''),
                            "prompt": prompt,
                            "post_title": post['title']
                        })
                        log(f"  ➕ @{c.get('author', {}).get('name', '')}")
                    else:
                        log(f"  ⏳ Rate limited: {reason}")
                        break
        
        return tasks
    
    def run(self):
        log("="*70)
        log("Moltbook Social v8.0")
        log("="*70)
        log("")
        
        # 准备任务
        tasks = self.prepare_tasks()
        
        if not tasks:
            log("✅ No pending tasks")
            return
        
        log("")
        log(f"Found {len(tasks)} tasks to process")
        log("⚠️  This script prepares tasks.")
        log("   Use sessions_spawn for each task, then send.")
        log("")
        
        # 保存任务供处理
        with open("/tmp/moltbook_tasks_v8.json", 'w') as f:
            json.dump(tasks, f, indent=2)
        
        log(f"Tasks saved: /tmp/moltbook_tasks_v8.json")
        log("")
        log("Next steps:")
        for i, t in enumerate(tasks[:2], 1):
            log(f"  {i}. Generate reply for @{t['author']} using sessions_spawn")
        if len(tasks) > 2:
            log(f"  ... and {len(tasks)-2} more")
        
        log("")
        log("="*70)

if __name__ == "__main__":
    agent = MoltbookSocialV8()
    agent.run()
