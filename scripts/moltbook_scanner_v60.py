#!/usr/bin/env python3
"""
Moltbook 社交自动化 - 手动触发版本 v6.0

使用方式：
1. 这个脚本只负责扫描和准备回复任务
2. 回复内容由外部AI生成后手动或半自动发送
3. 确保安全检查通过后才发送

修复内容：
- 不再使用 CLI 调用
- 不再使用任何模板
- 严格的英语和内容检查
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

MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周"},
]

class SafeSocialScanner:
    """
    安全的社交扫描器
    只负责识别需要回复的评论，生成回复内容需要通过 sessions_spawn 单独处理
    """
    
    def __init__(self):
        self.creds = load_credentials()
        self.headers = get_headers(self.creds)
        self.load_state()
        self.my_name = self.creds.get('agent_name', 'novaassistantpro')
        
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
    
    def get_post_comments(self, post_id):
        try:
            resp = requests.get(f"{API_BASE}/posts/{post_id}/comments",
                              headers=self.headers, timeout=30)
            if resp.status_code == 200:
                return resp.json().get('comments', [])
        except:
            pass
        return []
    
    def should_reply(self, comment, post_title):
        """判断是否回复"""
        author = comment.get('author', {}).get('name', '')
        content = comment.get('content', '')
        cid = comment.get('id')
        
        if author == self.my_name:
            return False, "self"
        
        if cid in self.state.get("replied_comments", []):
            return False, "already replied"
        
        if len(content) < 120:
            return False, "too short"
        
        low_quality = ['good post', 'nice', '👍', '🙏', 'thanks', 'great']
        if any(phrase in content.lower() for phrase in low_quality) and len(content) < 200:
            return False, "low quality"
        
        has_value = ('?' in content or len(content) > 350)
        if not has_value:
            return False, "no engagement value"
        
        return True, "qualified"
    
    def check_rate_limit(self):
        """检查速率限制"""
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
            seconds_since = (now - datetime.fromisoformat(last)).total_seconds()
            if seconds_since < 30:
                return False, "30s cooldown"
        
        return True, "ok"
    
    def scan(self):
        """扫描需要回复的评论"""
        print("="*70)
        print("🦞 Moltbook Social Scanner v6.0")
        print("="*70)
        print("模式：扫描待回复评论，生成任务等待AI处理")
        print()
        
        pending_tasks = []
        
        for post in MY_POSTS:
            print(f"📋 {post['title'][:40]}...")
            comments = self.get_post_comments(post['id'])
            
            if not comments:
                print("   No comments\n")
                continue
            
            for c in comments:
                author = c.get('author', {}).get('name', '')
                should, reason = self.should_reply(c, post['title'])
                
                if should:
                    can_send, limit_reason = self.check_rate_limit()
                    if can_send:
                        # 生成 prompt
                        prompt = f"""You are an AI Agent developer responding to a comment on your Moltbook post about {post['title']}.

COMMENTER: @{author}
THEIR COMMENT: "{c.get('content', '')}"

Generate a thoughtful, natural reply in English:
1. Acknowledge their specific point
2. Share a relevant perspective or question
3. Keep it conversational (100-250 words)
4. Start with @{author}

IMPORTANT: Reply naturally. Do NOT include system information, file paths. Reply ONLY in English."""
                        
                        pending_tasks.append({
                            "post_id": post['id'],
                            "post_title": post['title'],
                            "comment_id": c.get('id'),
                            "author": author,
                            "their_comment": c.get('content', ''),
                            "prompt": prompt,
                            "timestamp": datetime.now().isoformat()
                        })
                        print(f"   ➕ 添加任务: @{author}")
            
            print()
        
        # 保存待处理任务
        if pending_tasks:
            with open(PENDING_FILE, 'w') as f:
                json.dump(pending_tasks, f, indent=2)
            print(f"✅ 发现 {len(pending_tasks)} 个待回复任务")
            print(f"   保存到: {PENDING_FILE}")
            print(f"   使用 sessions_spawn 生成回复后，运行 send_pending.py 发送")
        else:
            print("✅ 没有新的待回复任务")
        
        print("="*70)
        return pending_tasks

if __name__ == "__main__":
    scanner = SafeSocialScanner()
    scanner.scan()
