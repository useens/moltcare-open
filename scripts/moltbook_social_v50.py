#!/usr/bin/env python3
"""
Moltbook 真社交自动化系统 v5.0 - 对话式社交模式
原则：只在对方回复我之后，我才回复对方（健康互动）
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
STATE_FILE = "/tmp/moltbook_social_state_v5.json"

MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周"},
    {"id": "cc41553f-7366-40ca-ba5c-18cb526a63dc", "title": "决策引擎完整学习闭环"},
]

class ConversationBasedSocialAgent:
    """
    对话式社交代理
    核心原则：只在对方回复我之后，我才回复对方
    """
    
    def __init__(self):
        self.creds = load_credentials()
        self.headers = get_headers(self.creds)
        self.load_state()
        self.my_name = self.creds.get('agent_name', 'novaassistantpro')
        
    def load_state(self):
        """加载状态，包括我发出的回复记录"""
        try:
            with open(STATE_FILE, 'r') as f:
                self.state = json.load(f)
        except:
            self.state = {
                "my_replies": {},  # comment_id -> {author, content, time, replied_by_author}
                "comment_times": [],
                "conversations": {}  # thread_id -> {started, last_reply_time, reply_count}
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
    
    def build_comment_tree(self, comments):
        """
        构建评论树，找出对话关系
        返回: {parent_id: [child_comments]}
        """
        tree = {}
        for c in comments:
            parent_id = c.get('parent_id')
            if parent_id:
                if parent_id not in tree:
                    tree[parent_id] = []
                tree[parent_id].append(c)
        return tree
    
    def find_replies_to_me(self, comments, comment_tree):
        """
        找出所有回复我的评论
        即：parent_id是我发的评论的评论
        """
        replies_to_me = []
        
        # 找出我发的所有评论的ID
        my_comment_ids = set()
        for c in comments:
            if c.get('author', {}).get('name') == self.my_name:
                my_comment_ids.add(c.get('id'))
        
        # 找出回复我的评论
        for c in comments:
            author = c.get('author', {}).get('name', '')
            parent_id = c.get('parent_id')
            
            # 如果是回复我的，且不是我自己的回复
            if parent_id in my_comment_ids and author != self.my_name:
                # 找到我的原始回复
                my_original = None
                for mc in comments:
                    if mc.get('id') == parent_id:
                        my_original = mc
                        break
                
                replies_to_me.append({
                    'reply': c,
                    'my_original': my_original,
                    'thread_id': parent_id
                })
        
        return replies_to_me
    
    def should_continue_conversation(self, thread_id, reply_count_in_thread):
        """
        判断是否应该继续这个对话
        """
        # 获取这个对话的历史
        conv = self.state.get("conversations", {}).get(thread_id, {})
        
        # 如果对话已经超过3轮，暂停（避免过度活跃）
        if reply_count_in_thread >= 3:
            return False, "conversation too long (3+ rounds)"
        
        # 检查最后回复时间，如果对方回复很及时，继续对话
        last_reply = conv.get('last_reply_time')
        if last_reply:
            last_time = datetime.fromisoformat(last_reply)
            hours_since = (datetime.now() - last_time).total_seconds() / 3600
            
            # 如果对方几小时内就回复了，说明对话很活跃，可以继续
            if hours_since < 24:
                return True, "active conversation"
            else:
                return False, "conversation stale (>24h)"
        
        return True, "new conversation"
    
    def generate_reply(self, author, their_reply, my_original, post_title):
        """生成回复，继续对话"""
        
        prompt = f"""You are an AI Agent developer continuing a conversation on Moltbook.

CONTEXT:
- Post: {post_title}
- You previously said: "{my_original.get('content', '')[:200]}"
- @{author} replied to you: "{their_reply.get('content', '')[:300]}"

TASK:
Continue this conversation naturally:
1. Acknowledge their specific response to your point
2. Answer any questions they asked or address their concerns
3. Share additional insight based on their feedback
4. Ask ONE follow-up question to keep the dialogue going
5. Keep it conversational, not like a broadcast

Generate your reply (start with @{author}):"""

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
        if len(recent) >= 5:
            return False
        
        last = self.state.get("last_comment_time")
        if last and (now - datetime.fromisoformat(last)).total_seconds() < 35:
            return False
        return True
    
    def run(self):
        print("="*70)
        print("🦞 Moltbook Social System v5.0 - Conversation Mode")
        print("="*70)
        print("💡 Principle: Only reply when someone replies to me")
        print("💡 Healthy interaction: They talk → I respond → They talk → I respond\n")
        
        total_replies_to_me = 0
        total_replied = 0
        total_skipped = 0
        
        for post in MY_POSTS:
            print(f"📋 {post['title'][:40]}...")
            comments = self.get_post_comments(post['id'])
            
            if not comments:
                print("   No comments\n")
                continue
            
            # 构建评论树
            comment_tree = self.build_comment_tree(comments)
            
            # 找出所有回复我的评论
            replies_to_me = self.find_replies_to_me(comments, comment_tree)
            
            print(f"   Total comments: {len(comments)}")
            print(f"   Replies to me: {len(replies_to_me)}")
            
            if not replies_to_me:
                print("   No one has replied to me yet\n")
                continue
            
            for item in replies_to_me:
                reply = item['reply']
                my_original = item['my_original']
                thread_id = item['thread_id']
                author = reply.get('author', {}).get('name', '')
                reply_id = reply.get('id')
                
                # 检查我是否已经回复过这条回复
                if reply_id in self.state.get("my_replies", {}):
                    print(f"   ⏭️  Already replied to @{author}'s reply")
                    total_skipped += 1
                    continue
                
                # 统计这个对话线程的轮数
                reply_count = 1  # 当前这条回复
                if thread_id in self.state.get("conversations", {}):
                    reply_count += self.state["conversations"][thread_id].get("reply_count", 0)
                
                # 判断是否继续对话
                should_reply, reason = self.should_continue_conversation(thread_id, reply_count)
                
                if not should_reply:
                    print(f"   ⏹️  Skipping @{author}: {reason}")
                    total_skipped += 1
                    continue
                
                print(f"\n   💬 @{author} replied to me:")
                print(f"      Their reply: {reply.get('content', '')[:80]}...")
                print(f"      Conversation round: {reply_count}")
                
                # 检查速率限制
                if not self.check_rate_limit():
                    print(f"      ⏳ Rate limited, skipping")
                    continue
                
                # 生成回复
                response = self.generate_reply(author, reply, my_original, post['title'])
                
                if response:
                    print(f"      My response: {response[:80]}...")
                    
                    # 发送回复
                    if self.reply_to_comment(post['id'], reply_id, response):
                        print(f"      ✅ Replied")
                        total_replied += 1
                        
                        # 更新状态
                        now_str = datetime.now().isoformat()
                        self.state.setdefault("comment_times", []).append(now_str)
                        self.state["last_comment_time"] = now_str
                        self.state.setdefault("my_replies", {})[reply_id] = {
                            "author": author,
                            "time": now_str,
                            "thread_id": thread_id
                        }
                        
                        # 更新对话记录
                        if thread_id not in self.state.setdefault("conversations", {}):
                            self.state["conversations"][thread_id] = {
                                "started": now_str,
                                "reply_count": 0
                            }
                        self.state["conversations"][thread_id]["reply_count"] = reply_count
                        self.state["conversations"][thread_id]["last_reply_time"] = now_str
                        
                        self.save_state()
                    else:
                        print(f"      ❌ Failed to send")
                else:
                    print(f"      ❌ AI generation failed")
                
                total_replies_to_me += 1
                time.sleep(35)
            
            print()
        
        print("="*70)
        print(f"✅ Summary:")
        print(f"   Replies to me found: {total_replies_to_me}")
        print(f"   Replied back: {total_replied}")
        print(f"   Skipped: {total_skipped}")
        print(f"   Active conversations: {len(self.state.get('conversations', {}))}")
        print("="*70)

if __name__ == "__main__":
    agent = ConversationBasedSocialAgent()
    agent.run()
