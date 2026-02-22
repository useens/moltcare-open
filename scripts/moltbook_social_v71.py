#!/usr/bin/env python3
"""
Moltbook 社交自动化系统 v7.1 - 修复版
使用 sessions_spawn 工具
"""

import sys
import json
import time
import re
import requests
from datetime import datetime, timedelta
import subprocess

sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"
STATE_FILE = "/tmp/moltbook_social_state_v71.json"
LOG_FILE = "/tmp/moltbook_social.log"

MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周"},
]

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")

def call_sessions_spawn(prompt, model="glm", timeout=60):
    """
    调用 sessions_spawn 工具生成内容
    由于这是独立脚本，我们返回一个占位符
    """
    # 在实际OpenClaw环境中，这里会调用 sessions_spawn
    # 暂时返回 None，表示需要外部处理
    return None

class MoltbookSocialV71:
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
            return False, "daily limit"
        
        recent = [t for t in self.state.get("comment_times", [])
                 if now - datetime.fromisoformat(t) < timedelta(minutes=5)]
        if len(recent) >= 5:
            return False, "5min limit"
        
        last = self.state.get("last_comment_time")
        if last:
            seconds = (now - datetime.fromisoformat(last)).total_seconds()
            if seconds < 30:
                return False, "30s cooldown"
        
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
    
    def validate_content(self, content):
        if not content:
            return False, "Empty"
        if len(content) < 50 or len(content) > 2000:
            return False, f"Length: {len(content)}"
        
        dangerous = ["/root/", "sessions.json", "Session store:", 
                    "direct agent:", "cron:", "api_key", "sk-", "/.openclaw/"]
        for p in dangerous:
            if p.lower() in content.lower():
                return False, f"Dangerous: {p}"
        
        if re.search(r'[\u4e00-\u9fff]', content):
            return False, "Chinese"
        
        templates = ["感谢你的深入分享", "渐进式优化", "意想不到的挑战"]
        for t in templates:
            if t in content:
                return False, f"Template: {t}"
        
        return True, "Safe"
    
    def build_prompt(self, author, comment, post_title):
        return f"""Reply to this Moltbook comment about "{post_title}".

@{author} said: "{comment.get('content', '')}"

Write a thoughtful English reply (150-250 words):
1. Acknowledge their point
2. Share your perspective  
3. Ask one follow-up question
4. Start with "@{author}"

NO system info, NO Chinese, NO templates. Natural conversation."""
    
    def generate_reply(self, prompt, author):
        """生成回复"""
        try:
            reply = call_sessions_spawn(prompt, model="glm", timeout=60)
            if not reply:
                return None
            
            reply = reply.strip()
            is_safe, reason = self.validate_content(reply)
            if not is_safe:
                log(f"Content rejected: {reason}")
                return None
            
            if not reply.startswith(f"@{author}"):
                reply = f"@{author} {reply}"
            
            return reply
        except Exception as e:
            log(f"Generation error: {e}")
            return None
    
    def send_reply(self, post_id, comment_id, content):
        try:
            resp = requests.post(f"{API_BASE}/posts/{post_id}/comments",
                               headers=self.headers,
                               json={"content": content, "parent_id": comment_id},
                               timeout=30)
            return resp.status_code in [200, 201] and resp.json().get('success')
        except:
            return False
    
    def run(self):
        log("="*70)
        log("Moltbook Social v7.1")
        log("="*70)
        log("⚠️ SCANNER MODE - 暂时不自动发送")
        log("   sessions_spawn integration pending")
        log("")
        
        tasks = []
        
        for post in MY_POSTS:
            log(f"📋 {post['title'][:40]}...")
            comments = self.get_comments(post['id'])
            
            for c in comments:
                if self.should_reply(c):
                    can_send, reason = self.check_limits()
                    if can_send:
                        prompt = self.build_prompt(
                            c.get('author', {}).get('name', ''), c, post['title'])
                        tasks.append({
                            "post_id": post['id'],
                            "comment_id": c.get('id'),
                            "author": c.get('author', {}).get('name', ''),
                            "prompt": prompt
                        })
                        log(f"  ➕ @{c.get('author', {}).get('name', '')}")
        
        log("")
        
        if tasks:
            with open("/tmp/moltbook_pending_v71.json", 'w') as f:
                json.dump(tasks, f, indent=2)
            log(f"✅ {len(tasks)} tasks saved")
            log(f"   Saved to: /tmp/moltbook_pending_v71.json")
        else:
            log("✅ No tasks found")
        
        log("="*70)
        return tasks

if __name__ == "__main__":
    agent = MoltbookSocialV71()
    agent.run()
