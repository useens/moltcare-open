#!/usr/bin/env python3
"""
Moltbook 真社交自动化系统 v4.1 - 防过度回复版
限制：每个帖子最多回复3条，优先高质量评论
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
AI_CACHE_FILE = "/tmp/moltbook_ai_cache.json"

MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation", "max_replies": 3},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal", "max_replies": 3},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility", "max_replies": 3},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周", "max_replies": 3},
    {"id": "cc41553f-7366-40ca-ba5c-18cb526a63dc", "title": "决策引擎完整学习闭环", "max_replies": 2},
]

class MoltbookSocialAgent:
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
            self.state = {"replied_comments": [], "comment_times": [], "post_reply_counts": {}}
    
    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f)
    
    def get_post_comments(self, post_id):
        try:
            resp = requests.get(f"{API_BASE}/posts/{post_id}/comments",
                              headers=self.headers, timeout=30)
            if resp.status_code == 200:
                return resp.json().get('comments', [])
        except:
            pass
        return []
    
    def count_my_replies_in_post(self, post_id, comments):
        """计算我在这个帖子下已回复的数量"""
        count = 0
        for c in comments:
            author = c.get('author', {}).get('name', '')
            if author == self.my_name:
                count += 1
        return count
    
    def should_reply(self, comment, post_id, post_comments, max_replies):
        """
        智能筛选：决定是否应该回复这条评论
        """
        author = comment.get('author', {}).get('name', '')
        content = comment.get('content', '')
        cid = comment.get('id')
        
        # 1. 检查是否已回复（本地状态）
        if cid in self.state.get("replied_comments", []):
            return False, "already replied"
        
        # 2. 检查帖子回复上限
        my_reply_count = self.count_my_replies_in_post(post_id, post_comments)
        if my_reply_count >= max_replies:
            return False, f"post limit reached ({my_reply_count}/{max_replies})"
        
        # 3. 质量筛选：评论长度
        if len(content) < 80:
            return False, "too short"
        
        # 4. 质量筛选：是否有实质内容（不是简单的"good post"）
        low_quality_phrases = ['good post', 'nice', 'thanks', 'great', '👍', '🙏']
        if any(phrase in content.lower() for phrase in low_quality_phrases) and len(content) < 100:
            return False, "low quality"
        
        # 5. 相关性筛选：是否与我的领域相关
        relevant_keywords = ['agent', 'memory', 'automation', 'cognitive', 'system', 
                           'blockchain', 'heartbeat', 'consciousness', 'architecture',
                           'format', 'silent failure', 'coordinator', 'infrastructure']
        if not any(kw in content.lower() for kw in relevant_keywords):
            return False, "not relevant"
        
        # 6. 互动价值：是否有深度讨论潜力
        has_question = '?' in content
        has_thinking = any(word in content.lower() for word in ['think', 'wonder', 'curious', 'question', 'how do you'])
        shares_experience = any(word in content.lower() for word in ['i have', 'my experience', 'i encountered', 'i faced'])
        
        if not (has_question or has_thinking or shares_experience):
            return False, "low engagement potential"
        
        # 7. 优先级排序加分项
        score = 0
        if shares_experience:
            score += 3  # 分享经验的优先回复
        if has_question:
            score += 2
        if len(content) > 200:
            score += 1  # 长评论通常更有深度
        
        return True, f"qualified (score: {score})"
    
    def generate_ai_reply(self, author, content, post_title):
        """调用真实AI生成回复"""
        # 构建prompt
        prompt = f"""You are an AI Agent developer engaging in technical discussion on Moltbook community.

POST: {post_title}
COMMENTER: @{author}
THEIR COMMENT: {content}

Generate a thoughtful, authentic reply (150-250 words) that:
1. Specifically acknowledges their point (not generic)
2. Responds to their experience/question
3. Shares your relevant insight
4. Asks 1 follow-up question to continue discussion
5. Professional but conversational tone

Reply (start with @{author}):"""

        try:
            print(f"   🤖 Calling AI...", end='', flush=True)
            result = subprocess.run(
                ['openclaw', 'sessions', 'spawn', '--model', 'glm', '--task', prompt],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0 and result.stdout.strip():
                reply = result.stdout.strip()
                if not reply.startswith(f"@{author}"):
                    reply = f"@{author} {reply}"
                print(" ✅")
                return reply
            else:
                print(f" ❌")
                return None
        except Exception as e:
            print(f" ❌ {e}")
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
    
    def run(self):
        print("="*70)
        print("🦞 Moltbook Social System v4.1 - Smart Filtering")
        print("="*70)
        print("🎯 Rules:")
        print("   - Max 3 replies per post")
        print("   - Only high-quality, relevant comments")
        print("   - Prioritize experience sharing & questions")
        print("   - Real AI generation (no templates)\n")
        
        total_qualified = 0
        total_replied = 0
        total_skipped = 0
        
        for post in MY_POSTS:
            print(f"📋 {post['title'][:40]}...")
            comments = self.get_post_comments(post['id'])
            
            # 统计我在这个帖子下已有的回复数
            my_existing = self.count_my_replies_in_post(post['id'], comments)
            remaining = post['max_replies'] - my_existing
            
            print(f"   Total: {len(comments)} | My replies: {my_existing}/{post['max_replies']}")
            
            if remaining <= 0:
                print(f"   ⏹️  Already reached limit, skipping")
                continue
            
            # 筛选可回复的评论
            qualified = []
            for c in comments:
                author = c.get('author', {}).get('name', '')
                if author == self.my_name:
                    continue
                
                should, reason = self.should_reply(c, post['id'], comments, post['max_replies'])
                if should:
                    qualified.append((c, reason))
                else:
                    total_skipped += 1
            
            # 按质量排序，优先回复高质量的
            qualified.sort(key=lambda x: int(x[1].split('score: ')[1].rstrip(')')) if 'score:' in x[1] else 0, reverse=True)
            
            # 只取前remaining个
            to_reply = qualified[:remaining]
            
            if not to_reply:
                print(f"   No qualified comments")
                continue
            
            print(f"   Qualified: {len(qualified)} | Will reply: {len(to_reply)}\n")
            
            for i, (c, reason) in enumerate(to_reply):
                author = c.get('author', {}).get('name', '')
                cid = c.get('id')
                content = c.get('content', '')
                
                print(f"   💬 [{i+1}/{len(to_reply)}] @{author}")
                print(f"      Reason: {reason}")
                print(f"      Preview: {content[:60]}...")
                
                # 生成AI回复
                reply = self.generate_ai_reply(author, content, post['title'])
                
                if reply:
                    print(f"      Generated: {reply[:70]}...")
                    
                    # 发送回复
                    if self.reply_to_comment(post['id'], cid, reply):
                        print(f"      ✅ Sent")
                        total_replied += 1
                        
                        # 更新状态
                        now_str = datetime.now().isoformat()
                        self.state.setdefault("comment_times", []).append(now_str)
                        self.state.setdefault("replied_comments", []).append(cid)
                        self.save_state()
                    else:
                        print(f"      ❌ Failed to send")
                else:
                    print(f"      ❌ AI generation failed")
                
                total_qualified += 1
                
                if i < len(to_reply) - 1:
                    time.sleep(35)
            
            print()
        
        print("="*70)
        print(f"✅ Summary:")
        print(f"   Qualified: {total_qualified}")
        print(f"   Replied: {total_replied}")
        print(f"   Skipped: {total_skipped}")
        print(f"   Total my replies today: {len(self.state.get('replied_comments', []))}")
        print("="*70)

if __name__ == "__main__":
    agent = MoltbookSocialAgent()
    agent.run()
