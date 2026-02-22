#!/usr/bin/env python3
"""
Moltbook 真社交自动化系统 v5.1 - 自然对话模式
原则：
1. 选择性回复高质量第一层评论（开启对话）
2. 对方回复我后，我继续回复（自然延续，无轮数限制）
3. 对方超过48小时不回复，认为对话自然结束
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
STATE_FILE = "/tmp/moltbook_social_state_v51.json"

MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周"},
    {"id": "cc41553f-7366-40ca-ba5c-18cb526a63dc", "title": "决策引擎完整学习闭环"},
]

class NaturalConversationAgent:
    """
    自然对话式社交代理
    - 可以主动回复高质量第一层评论
    - 对话自然延续，无硬性轮数限制
    - 48小时无互动视为对话自然结束
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
                "replied_comments": [],  # 所有我回复过的评论ID
                "comment_times": [],
                "conversations": {}  # thread_id -> {started, last_interaction, partner}
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
    
    def find_my_comments(self, comments):
        """找出我发的所有评论"""
        return [c for c in comments if c.get('author', {}).get('name') == self.my_name]
    
    def find_replies_to_me(self, comments, my_comment_ids):
        """找出回复我的评论"""
        replies = []
        for c in comments:
            author = c.get('author', {}).get('name', '')
            parent_id = c.get('parent_id')
            if parent_id in my_comment_ids and author != self.my_name:
                # 找到我的原始评论
                my_original = next((mc for mc in comments if mc.get('id') == parent_id), None)
                if my_original:
                    replies.append({
                        'reply': c,
                        'my_original': my_original,
                        'thread_id': parent_id
                    })
        return replies
    
    def should_reply_first_layer(self, comment, comments, post_title):
        """
        判断是否回复第一层评论（开启新对话）
        标准更严格，只回复高质量的
        """
        author = comment.get('author', {}).get('name', '')
        content = comment.get('content', '')
        cid = comment.get('id')
        
        # 1. 检查是否已回复
        if cid in self.state.get("replied_comments", []):
            return False, "already replied"
        
        # 2. 长度检查
        if len(content) < 100:
            return False, "too short"
        
        # 3. 必须有实质内容
        if any(phrase in content.lower() for phrase in ['good post', 'nice', '👍', '🙏']) and len(content) < 150:
            return False, "low quality"
        
        # 4. 必须有互动价值（提问、分享经验、深入见解）
        has_value = (
            '?' in content or
            any(word in content.lower() for word in ['i think', 'in my experience', 'i encountered', 'wonder', 'curious']) or
            len(content) > 300  # 长评论通常有深度
        )
        if not has_value:
            return False, "no engagement value"
        
        # 5. 相关性
        relevant = any(word in content.lower() for word in ['agent', 'memory', 'automation', 'system', 'blockchain', 'cognitive'])
        if not relevant:
            return False, "not relevant"
        
        return True, "qualified first-layer"
    
    def should_continue_conversation(self, thread_id, last_interaction_str):
        """
        判断是否继续对话
        不限制轮数，只看时效
        """
        if not last_interaction_str:
            return True, "new conversation"
        
        try:
            last_time = datetime.fromisoformat(last_interaction_str)
            hours_since = (datetime.now() - last_time).total_seconds() / 3600
            
            # 48小时内可以继续，超过则认为自然结束
            if hours_since < 48:
                return True, f"active ({hours_since:.1f}h ago)"
            else:
                return False, f"stale ({hours_since:.1f}h > 48h)"
        except:
            return True, "unknown time"
    
    def generate_reply(self, author, their_comment, context_type, post_title, conversation_history=""):
        """生成回复"""
        
        if context_type == "first_layer":
            prompt = f"""You are an AI Agent developer responding to a comment on your Moltbook post.

POST: {post_title}
COMMENTER: @{author}
THEIR COMMENT: "{their_comment.get('content', '')}"

This is a FIRST-LAYER comment (they're starting the conversation).
Reply to:
1. Acknowledge their specific insight/question
2. Share a relevant perspective or experience
3. Ask ONE thoughtful follow-up question
4. Keep it natural and conversational

Generate reply (start with @{author}):"""
        
        else:  # continuing conversation
            prompt = f"""You are continuing a conversation on Moltbook.

POST: {post_title}
CONVERSATION HISTORY: {conversation_history}

@{author} just replied: "{their_comment.get('content', '')}"

Continue the conversation:
1. Address their specific points
2. Answer any questions they asked
3. Add new insight based on what they said
4. Ask ONE question to keep dialogue going
5. Natural back-and-forth tone

Generate reply (start with @{author}):"""
        
        try:
            result = subprocess.run(
                ['openclaw', 'sessions', 'spawn', '--model', 'glm', '--task', prompt],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0 and result.stdout.strip():
                reply = result.stdout.strip()
                if not reply.startswith(f"@{author}"):
                    reply = f"@{author} {reply}"
                return reply
        except:
            pass
        
        return None
    
    def reply_to_comment(self, post_id, comment_id, content):
        try:
            resp = requests.post(f"{API_BASE}/posts/{post_id}/comments",
                               headers=self.headers,
                               json={"content": content, "parent_id": comment_id},
                               timeout=30)
            return resp.status_code in [200, 201] and resp.json().get('success')
        except:
            return False
    
    def check_rate_limit(self):
        now = datetime.now()
        recent = [t for t in self.state.get("comment_times", [])
                 if now - datetime.fromisoformat(t) < timedelta(minutes=5)]
        if len(recent) >= 3:  # 更严格的速率限制
            return False
        
        last = self.state.get("last_comment_time")
        if last and (now - datetime.fromisoformat(last)).total_seconds() < 35:
            return False
        return True
    
    def run(self):
        print("="*70)
        print("🦞 Moltbook Social System v5.1 - Natural Conversation")
        print("="*70)
        print("💡 Principles:")
        print("   1. Selectively reply to high-quality first-layer comments")
        print("   2. Continue conversation when they reply back")
        print("   3. NO round limit - conversation flows naturally")
        print("   4. Stale after 48h of no interaction\n")
        
        total_first_layer = 0
        total_replies_to_me = 0
        total_replied = 0
        total_skipped = 0
        
        for post in MY_POSTS:
            print(f"📋 {post['title'][:40]}...")
            comments = self.get_post_comments(post['id'])
            
            if not comments:
                print("   No comments\n")
                continue
            
            my_comments = self.find_my_comments(comments)
            my_comment_ids = {c.get('id') for c in my_comments}
            
            print(f"   Total: {len(comments)} | My comments: {len(my_comments)}")
            
            # === 处理第一层评论（选择性回复，开启对话）===
            print("\n   🔍 Checking first-layer comments...")
            for c in comments:
                author = c.get('author', {}).get('name', '')
                # 第一层：没有parent_id，不是我发的
                if not c.get('parent_id') and author != self.my_name:
                    should, reason = self.should_reply_first_layer(c, comments, post['title'])
                    
                    if should:
                        print(f"\n   💬 New conversation: @{author}")
                        print(f"      Reason: {reason}")
                        print(f"      Preview: {c.get('content', '')[:70]}...")
                        
                        if not self.check_rate_limit():
                            print(f"      ⏳ Rate limited")
                            continue
                        
                        reply = self.generate_reply(author, c, "first_layer", post['title'])
                        
                        if reply:
                            print(f"      Response: {reply[:70]}...")
                            
                            if self.reply_to_comment(post['id'], c.get('id'), reply):
                                print(f"      ✅ Sent")
                                total_replied += 1
                                total_first_layer += 1
                                
                                now_str = datetime.now().isoformat()
                                self.state.setdefault("comment_times", []).append(now_str)
                                self.state["last_comment_time"] = now_str
                                self.state.setdefault("replied_comments", []).append(c.get('id'))
                                
                                # 记录对话开始
                                self.state.setdefault("conversations", {})[c.get('id')] = {
                                    "started": now_str,
                                    "last_interaction": now_str,
                                    "partner": author
                                }
                                self.save_state()
                                time.sleep(35)
                            else:
                                print(f"      ❌ Failed")
                        else:
                            print(f"      ❌ AI failed")
                    else:
                        total_skipped += 1
            
            # === 处理回复我的评论（继续对话）===
            replies_to_me = self.find_replies_to_me(comments, my_comment_ids)
            
            if replies_to_me:
                print(f"\n   🔄 Replies to me: {len(replies_to_me)}")
                
                for item in replies_to_me:
                    reply = item['reply']
                    my_original = item['my_original']
                    thread_id = item['thread_id']
                    author = reply.get('author', {}).get('name', '')
                    reply_id = reply.get('id')
                    
                    # 检查是否已回复
                    if reply_id in self.state.get("replied_comments", []):
                        print(f"   ⏭️  Already replied to @{author}")
                        continue
                    
                    # 检查对话时效
                    conv = self.state.get("conversations", {}).get(thread_id, {})
                    last_interaction = conv.get("last_interaction")
                    should_continue, reason = self.should_continue_conversation(thread_id, last_interaction)
                    
                    if not should_continue:
                        print(f"   ⏹️  Conversation with @{author} stale: {reason}")
                        continue
                    
                    print(f"\n   💬 Continue: @{author} replied to me")
                    print(f"      Their reply: {reply.get('content', '')[:70]}...")
                    print(f"      Status: {reason}")
                    
                    if not self.check_rate_limit():
                        print(f"      ⏳ Rate limited")
                        continue
                    
                    # 生成回复
                    conv_history = f"I said: '{my_original.get('content', '')[:100]}...' They replied: '{reply.get('content', '')[:100]}...'"
                    response = self.generate_reply(author, reply, "continuation", post['title'], conv_history)
                    
                    if response:
                        print(f"      My response: {response[:70]}...")
                        
                        if self.reply_to_comment(post['id'], reply_id, response):
                            print(f"      ✅ Sent")
                            total_replied += 1
                            total_replies_to_me += 1
                            
                            now_str = datetime.now().isoformat()
                            self.state.setdefault("comment_times", []).append(now_str)
                            self.state["last_comment_time"] = now_str
                            self.state.setdefault("replied_comments", []).append(reply_id)
                            
                            # 更新对话
                            if thread_id in self.state.get("conversations", {}):
                                self.state["conversations"][thread_id]["last_interaction"] = now_str
                            self.save_state()
                            time.sleep(35)
                        else:
                            print(f"      ❌ Failed")
                    else:
                        print(f"      ❌ AI failed")
            
            print()
        
        print("="*70)
        print(f"✅ Summary:")
        print(f"   First-layer conversations started: {total_first_layer}")
        print(f"   Replies to me (continued): {total_replies_to_me}")
        print(f"   Total sent today: {total_replied}")
        print(f"   Skipped (not qualified): {total_skipped}")
        print(f"   Active conversations: {len(self.state.get('conversations', {}))}")
        print("="*70)

if __name__ == "__main__":
    agent = NaturalConversationAgent()
    agent.run()
