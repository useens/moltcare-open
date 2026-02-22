#!/usr/bin/env python3
"""
Moltbook 真社交自动化系统 v4.0 - 真实AI生成版
使用 sessions_spawn 调用真实AI模型生成回复
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
REPLY_LOG_FILE = "/tmp/moltbook_reply_log.jsonl"
AI_CACHE_FILE = "/tmp/moltbook_ai_cache.json"

MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周"},
    {"id": "cc41553f-7366-40ca-ba5c-18cb526a63dc", "title": "决策引擎完整学习闭环"},
]

class RealAIReplyGenerator:
    """使用真实AI模型生成回复"""
    
    def __init__(self):
        self.cache = self._load_cache()
    
    def _load_cache(self):
        try:
            with open(AI_CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_cache(self):
        with open(AI_CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _build_prompt(self, comment_author, comment_content, post_title):
        """构建给AI的prompt"""
        return f"""You are an AI Agent developer engaging in technical discussion on Moltbook community.

POST CONTEXT:
- Post title: {post_title}
- Commenter: @{comment_author}
- Their comment: {comment_content}

TASK:
Generate a thoughtful, authentic reply in English that:
1. Acknowledges or appreciates their specific point
2. Responds meaningfully to 1-2 key aspects of their comment
3. Shares your own relevant experience or insight
4. Asks 1-2 open-ended follow-up questions
5. Maintains friendly, professional technical tone
6. Length: 150-300 words

IMPORTANT:
- Be specific to what they said, not generic
- Show genuine curiosity about their perspective
- The goal is to continue a meaningful conversation

Generate the reply now (start with @{comment_author}):"""

    def generate(self, comment_author, comment_content, post_title, max_retries=2):
        """调用真实AI生成回复"""
        
        # 构建cache key
        cache_key = hashlib.md5(f"{comment_author}:{comment_content[:100]}:{post_title}".encode()).hexdigest()
        
        # 检查缓存
        if cache_key in self.cache:
            print(f"   💾 Using cached AI reply")
            return self.cache[cache_key]
        
        prompt = self._build_prompt(comment_author, comment_content, post_title)
        
        # 调用真实AI模型（使用openclaw sessions spawn）
        for attempt in range(max_retries):
            try:
                print(f"   🤖 Calling AI model (attempt {attempt+1})...")
                
                # 使用subprocess调用openclaw命令
                result = subprocess.run(
                    ['openclaw', 'sessions', 'spawn', 
                     '--model', 'glm',
                     '--task', prompt,
                     '--timeout', '60'],
                    capture_output=True,
                    text=True,
                    timeout=90
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    reply = result.stdout.strip()
                    
                    # 确保以@author开头
                    if not reply.startswith(f"@{comment_author}"):
                        reply = f"@{comment_author} {reply}"
                    
                    # 缓存回复
                    self.cache[cache_key] = reply
                    self._save_cache()
                    
                    print(f"   ✅ AI generated successfully")
                    return reply
                else:
                    print(f"   ⚠️ AI call failed: {result.stderr[:100]}")
                    
            except subprocess.TimeoutExpired:
                print(f"   ⏱️ AI call timeout")
            except Exception as e:
                print(f"   ❌ AI call error: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(5)
        
        # 所有尝试失败，返回错误标记（不使用模板）
        print(f"   ❌ AI generation failed after {max_retries} attempts")
        return None


class MoltbookSocialAgent:
    def __init__(self):
        self.creds = load_credentials()
        self.headers = get_headers(self.creds)
        self.ai = RealAIReplyGenerator()
        self.load_state()
        self.my_name = self.creds.get('agent_name', 'novaassistantpro')
        
    def load_state(self):
        try:
            with open(STATE_FILE, 'r') as f:
                self.state = json.load(f)
        except:
            self.state = {"replied_comments": [], "comment_times": []}
    
    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f)
    
    def log_reply(self, comment_id, author, success, error=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "comment_id": comment_id,
            "author": author,
            "success": success,
            "error": error
        }
        with open(REPLY_LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_post_comments(self, post_id):
        try:
            resp = requests.get(f"{API_BASE}/posts/{post_id}/comments",
                              headers=self.headers, timeout=30)
            if resp.status_code == 200:
                return resp.json().get('comments', [])
        except:
            pass
        return []
    
    def check_already_replied(self, comments, parent_comment_id):
        for c in comments:
            author = c.get('author', {}).get('name', '')
            parent_id = c.get('parent_id')
            if author == self.my_name and parent_id == parent_comment_id:
                return True, c.get('id')
        return False, None
    
    def check_rate_limit(self):
        now = datetime.now()
        recent = [t for t in self.state.get("comment_times", [])
                 if now - datetime.fromisoformat(t) < timedelta(minutes=5)]
        if len(recent) >= 5:
            return False, "rate limit"
        
        last_comment = self.state.get("last_comment_time")
        if last_comment:
            elapsed = (now - datetime.fromisoformat(last_comment)).total_seconds()
            if elapsed < 35:
                return False, f"wait {35-elapsed:.0f}s"
        return True, "ok"
    
    def reply_to_comment(self, post_id, post_comments, comment_id, author, content):
        # 检查1: 本地状态
        if comment_id in self.state.get("replied_comments", []):
            self.log_reply(comment_id, author, False, "already in local state")
            return False, "already replied"
        
        # 检查2: API验证
        already_replied, _ = self.check_already_replied(post_comments, comment_id)
        if already_replied:
            self.state.setdefault("replied_comments", []).append(comment_id)
            self.save_state()
            self.log_reply(comment_id, author, False, "already replied (API)")
            return False, "already replied"
        
        # 检查3: 速率限制
        can_proceed, reason = self.check_rate_limit()
        if not can_proceed:
            self.log_reply(comment_id, author, False, reason)
            return False, reason
        
        # 调用真实AI生成回复
        reply = self.ai.generate(author, content, post_comments[0].get('post', {}).get('title', 'Post') if post_comments else 'Post')
        
        if reply is None:
            self.log_reply(comment_id, author, False, "AI generation failed")
            return False, "AI failed"
        
        # 发送回复
        try:
            resp = requests.post(f"{API_BASE}/posts/{post_id}/comments",
                               headers=self.headers,
                               json={"content": reply, "parent_id": comment_id},
                               timeout=30)
            
            if resp.status_code in [200, 201] and resp.json().get('success'):
                now_str = datetime.now().isoformat()
                self.state.setdefault("comment_times", []).append(now_str)
                self.state["last_comment_time"] = now_str
                self.state.setdefault("replied_comments", []).append(comment_id)
                self.save_state()
                self.log_reply(comment_id, author, True)
                return True, "success"
            else:
                error = f"HTTP {resp.status_code}"
                self.log_reply(comment_id, author, False, error)
                return False, error
                
        except Exception as e:
            self.log_reply(comment_id, author, False, str(e))
            return False, str(e)
    
    def run(self):
        print("="*70)
        print("🦞 Moltbook Social System v4.0 - REAL AI")
        print("="*70)
        print("⚠️  Using REAL AI model (GLM) for reply generation")
        print("⚠️  NO TEMPLATES - All replies are AI-generated\n")
        
        total_new = 0
        total_replied = 0
        total_failed = 0
        
        for post in MY_POSTS:
            print(f"📋 {post['title'][:40]}...")
            comments = self.get_post_comments(post['id'])
            
            new_comments = []
            for c in comments:
                author = c.get('author', {}).get('name', '')
                cid = c.get('id')
                if author != self.my_name and cid not in self.state.get("replied_comments", []):
                    new_comments.append({
                        "post_id": post['id'],
                        "post_comments": comments,
                        "comment_id": cid,
                        "author": author,
                        "content": c.get('content', '')
                    })
            
            if not new_comments:
                print("   No new comments")
                continue
            
            print(f"   Found {len(new_comments)} new comments")
            
            for i, c in enumerate(new_comments):
                print(f"\n   💬 [{i+1}/{len(new_comments)}] @{c['author']}")
                
                success, msg = self.reply_to_comment(
                    c['post_id'], 
                    c['post_comments'],
                    c['comment_id'], 
                    c['author'], 
                    c['content']
                )
                
                if success:
                    print(f"   ✅ AI reply sent")
                    total_replied += 1
                elif "already replied" in msg:
                    print(f"   ⚠️ Skipped (already replied)")
                else:
                    print(f"   ❌ {msg}")
                    total_failed += 1
                
                if i < len(new_comments) - 1:
                    time.sleep(35)
            
            total_new += len(new_comments)
        
        print(f"\n{'='*70}")
        print(f"✅ Done: Replied {total_replied}/{total_new}")
        print(f"❌ Failed: {total_failed}")
        print(f"⚠️  Using REAL AI - NO TEMPLATES")
        print(f"{'='*70}")

if __name__ == "__main__":
    agent = MoltbookSocialAgent()
    agent.run()
