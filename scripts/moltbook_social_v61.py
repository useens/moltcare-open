#!/usr/bin/env python3
"""
Moltbook 社交自动化 v6.1 - 集成 sessions_spawn 版本

此版本通过调用 sessions_spawn 工具来生成回复
需要在 OpenClaw 环境中运行
"""

import sys
import json
import time
import requests
import re
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

# API配置
API_BASE = "https://www.moltbook.com/api/v1"
STATE_FILE = "/tmp/moltbook_social_state_v61.json"

# 我的帖子列表
MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周"},
]

class SafeSocialAutomation:
    """安全的社交自动化 v6.1"""
    
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
            return False, "Daily limit"
        
        recent_5min = [t for t in self.state.get("comment_times", [])
                      if now - datetime.fromisoformat(t) < timedelta(minutes=5)]
        if len(recent_5min) >= 5:
            return False, "5-min limit"
        
        last = self.state.get("last_comment_time")
        if last:
            seconds = (now - datetime.fromisoformat(last)).total_seconds()
            if seconds < 30:
                return False, f"30s cooldown ({seconds:.0f}s)"
        
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
    
    def validate_reply(self, content):
        if not content:
            return False, "Empty"
        if len(content) < 50 or len(content) > 2000:
            return False, f"Length: {len(content)}"
        
        dangerous = ["/root/", "sessions.json", "Session store:", "direct agent:", "cron:"]
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
        return f"""Reply to this comment on Moltbook about "{post_title}".

@{author} said: "{comment.get('content', '')}"

Write a thoughtful English reply (150-250 words):
1. Acknowledge their specific point
2. Share your perspective
3. Ask one follow-up question
4. Start with "@{author}"

NO system info, NO Chinese, NO templates. Natural conversation only."""
    
    def send_reply(self, post_id, comment_id, content):
        try:
            resp = requests.post(f"{API_BASE}/posts/{post_id}/comments",
                               headers=self.headers,
                               json={"content": content, "parent_id": comment_id},
                               timeout=30)
            return resp.status_code in [200, 201] and resp.json().get('success')
        except:
            return False
    
    def process_single_task(self, post, comment):
        """处理单个任务 - 可以被主会话调用"""
        author = comment.get('author', {}).get('name', '')
        
        print(f"\n处理: @{author}")
        print(f"  评论: {comment.get('content', '')[:60]}...")
        
        # 检查限制
        can_send, reason = self.check_limits()
        if not can_send:
            print(f"  ⏳ 跳过: {reason}")
            return False
        
        # 构建prompt
        prompt = self.build_prompt(author, comment, post['title'])
        
        # 生成回复 - 返回prompt供外部处理
        return {
            "post_id": post['id'],
            "comment_id": comment.get('id'),
            "author": author,
            "prompt": prompt,
            "requires_generation": True
        }
    
    def run(self):
        print("="*70)
        print("🦞 Moltbook Social v6.1")
        print("="*70)
        
        pending = []
        
        for post in MY_POSTS:
            print(f"\n📋 {post['title'][:40]}...")
            comments = self.get_comments(post['id'])
            
            for c in comments:
                if self.should_reply(c):
                    result = self.process_single_task(post, c)
                    if result:
                        pending.append(result)
        
        print(f"\n✅ 发现 {len(pending)} 个待处理任务")
        
        if pending:
            # 保存任务
            with open("/tmp/moltbook_pending_v61.json", 'w') as f:
                json.dump(pending, f, indent=2)
            print(f"   任务已保存: /tmp/moltbook_pending_v61.json")
            print("\n请运行 generate_replies_v61.py 生成回复")
        
        print("="*70)
        return pending

if __name__ == "__main__":
    agent = SafeSocialAutomation()
    agent.run()
