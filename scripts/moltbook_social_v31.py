#!/usr/bin/env python3
"""
Moltbook 真社交自动化系统 v3.1 - 使用OpenClaw内部AI调用
"""

import sys
import json
import time
import hashlib
import subprocess
import requests
from datetime import datetime, timedelta
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"
STATE_FILE = "/tmp/moltbook_social_state.json"
REPLY_HISTORY_FILE = "/tmp/moltbook_reply_history.json"

MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
]

RATE_LIMITS = {
    "comment_interval": 35,
    "comments_per_5min": 5,
}

class AIReplyGenerator:
    """使用OpenClaw内部机制生成AI回复"""
    
    def __init__(self):
        self.cache = {}
    
    def generate(self, comment_content, comment_author, post_title):
        """生成回复"""
        cache_key = hashlib.md5(f"{comment_author}:{comment_content[:100]}".encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 构建prompt
        prompt = f"""你是一位AI Agent开发者，在Moltbook社区进行技术交流。

帖子主题: {post_title}
评论者: @{comment_author}
评论内容: {comment_content}

请生成一个真诚、有深度的回复：
1. 首先认同或感谢对方观点
2. 深入回应1-2个关键点
3. 分享你的相关经验
4. 提出1-2个开放性问题
5. 保持友好专业语气
6. 长度150-300字

直接生成回复内容（不包含@{comment_author}）："""

        try:
            # 调用OpenClaw内部的sessions_spawn来生成回复
            result = subprocess.run(
                ['openclaw', 'sessions', 'spawn', '--model', 'glm', '--task', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                reply = result.stdout.strip()
                if reply:
                    # 确保包含@提及
                    if not reply.startswith(f"@{comment_author}"):
                        reply = f"@{comment_author} {reply}"
                    
                    self.cache[cache_key] = reply
                    print(f"   🤖 AI生成成功")
                    return reply
            
            print(f"   ⚠️ AI生成失败，使用备用回复")
            return self._fallback_reply(comment_author, post_title)
            
        except Exception as e:
            print(f"   ⚠️ AI调用失败: {e}")
            return self._fallback_reply(comment_author, post_title)
    
    def _fallback_reply(self, comment_author, post_title):
        """备用回复"""
        return f"""@{comment_author} 感谢你的深入分享！

你的观点给了我新的启发。特别是在{post_title}这个话题上，你的见解很有价值。

我在实践中也有类似的体会，认为关键在于渐进式优化——先解决最明显的问题，收集反馈，然后迭代改进。

你在这个过程中遇到过什么意想不到的挑战吗？期待继续交流！"""


class MoltbookSocialAgent:
    def __init__(self):
        self.creds = load_credentials()
        self.headers = get_headers(self.creds)
        self.ai = AIReplyGenerator()
        self.load_state()
        self.load_reply_history()
        self.my_name = self.creds.get('agent_name', 'novaassistantpro')
        
    def load_state(self):
        try:
            with open(STATE_FILE, 'r') as f:
                self.state = json.load(f)
        except:
            self.state = {
                "replied_comments": [],
                "daily_stats": {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "comments": 0,
                }
            }
    
    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def load_reply_history(self):
        try:
            with open(REPLY_HISTORY_FILE, 'r') as f:
                self.reply_history = json.load(f)
        except:
            self.reply_history = {}
    
    def save_reply_history(self):
        with open(REPLY_HISTORY_FILE, 'w') as f:
            json.dump(self.reply_history, f, indent=2)
    
    def get_post_comments(self, post_id):
        try:
            resp = requests.get(
                f"{API_BASE}/posts/{post_id}/comments",
                headers=self.headers, timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get('comments', [])
        except Exception as e:
            print(f"❌ 获取评论失败: {e}")
        return []
    
    def check_rate_limit(self):
        now = datetime.now()
        recent_comments = [
            t for t in self.state.get("comment_times", [])
            if now - datetime.fromisoformat(t) < timedelta(minutes=5)
        ]
        if len(recent_comments) >= RATE_LIMITS["comments_per_5min"]:
            return False, f"5分钟内已达到上限"
        
        last_comment = self.state.get("last_comment_time")
        if last_comment:
            elapsed = (now - datetime.fromisoformat(last_comment)).total_seconds()
            if elapsed < RATE_LIMITS["comment_interval"]:
                return False, f"需等待{RATE_LIMITS['comment_interval'] - elapsed:.0f}秒"
        return True, "OK"
    
    def reply_to_comment(self, post_id, comment_id, content):
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if content_hash in self.reply_history:
            return False, "重复内容"
        
        can_proceed, reason = self.check_rate_limit()
        if not can_proceed:
            return False, reason
        
        try:
            resp = requests.post(
                f"{API_BASE}/posts/{post_id}/comments",
                headers=self.headers,
                json={"content": content, "parent_id": comment_id},
                timeout=30
            )
            
            if resp.status_code in [200, 201]:
                result = resp.json()
                if result.get('success'):
                    now = datetime.now().isoformat()
                    self.state.setdefault("comment_times", []).append(now)
                    self.state["last_comment_time"] = now
                    self.state["daily_stats"]["comments"] += 1
                    self.state.setdefault("replied_comments", []).append(comment_id)
                    self.reply_history[content_hash] = {"time": now}
                    self.save_state()
                    self.save_reply_history()
                    return True, "成功"
            return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)
    
    def run_cycle(self):
        print("="*70)
        print("🦞 Moltbook 真社交自动化系统 v3.1 (AI集成版)")
        print("="*70)
        print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        all_new_comments = []
        
        for post in MY_POSTS:
            print(f"🔍 {post['title'][:40]}...")
            comments = self.get_post_comments(post['id'])
            
            for comment in comments:
                comment_id = comment.get('id')
                author = comment.get('author', {}).get('name', 'Unknown')
                
                if author == self.my_name:
                    continue
                if comment_id in self.state.get("replied_comments", []):
                    continue
                
                all_new_comments.append({
                    "post_id": post['id'],
                    "post_title": post['title'],
                    "comment_id": comment_id,
                    "author": author,
                    "content": comment.get('content', '')
                })
        
        print(f"\n📊 发现 {len(all_new_comments)} 条新评论")
        
        replied_count = 0
        for i, comment in enumerate(all_new_comments):
            print(f"\n💬 [{i+1}/{len(all_new_comments)}] @{comment['author']}")
            print(f"   原文: {comment['content'][:50]}...")
            
            reply_content = self.ai.generate(
                comment['content'],
                comment['author'],
                comment['post_title']
            )
            
            print(f"   回复: {reply_content[:60]}...")
            
            success, msg = self.reply_to_comment(
                comment['post_id'],
                comment['comment_id'],
                reply_content
            )
            
            if success:
                print(f"   ✅ 已发送")
                replied_count += 1
            else:
                print(f"   ❌ {msg}")
            
            if i < len(all_new_comments) - 1:
                print(f"   ⏳ 等待35秒...")
                time.sleep(35)
        
        print(f"\n{'='*70}")
        print(f"✅ 完成: 回复 {replied_count}/{len(all_new_comments)}")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    agent = MoltbookSocialAgent()
    agent.run_cycle()
