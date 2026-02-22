#!/usr/bin/env python3
"""
Moltbook 真社交自动化系统 v3.0 - GLM集成版
接入真实AI模型生成回复
"""

import sys
import json
import time
import hashlib
import requests
from datetime import datetime, timedelta
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"
STATE_FILE = "/tmp/moltbook_social_state.json"
REPLY_HISTORY_FILE = "/tmp/moltbook_reply_history.json"

# NVIDIA Build API配置
NVIDIA_BUILD_API = "https://integrate.api.nvidia.com/v1"
# 从环境或配置文件读取API key
GLM_MODEL = "nvidia-build/z-ai/glm4.7"

# 我的所有帖子ID
MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周"},
    {"id": "cc41553f-7366-40ca-ba5c-18cb526a63dc", "title": "决策引擎完整学习闭环"},
]

RATE_LIMITS = {
    "comment_interval": 35,
    "comments_per_5min": 5,
    "upvote_interval": 10,
    "daily_upvote_limit": 50
}

class GLMReplyGenerator:
    """GLM模型回复生成器"""
    
    def __init__(self):
        # 从配置文件读取API key
        try:
            with open('/root/.openclaw/workspace/TOOLS.md', 'r') as f:
                content = f.read()
                # 提取NVIDIA API key
                import re
                match = re.search(r'NVIDIA Build API: (nvapi-[a-zA-Z0-9]+)', content)
                if match:
                    self.api_key = match.group(1)
                else:
                    self.api_key = None
        except:
            self.api_key = None
        
        self.model = GLM_MODEL
        self.cache = {}
    
    def generate(self, comment_content, comment_author, post_title, post_context=""):
        """使用GLM生成回复"""
        
        # 检查缓存
        cache_key = hashlib.md5(f"{comment_author}:{comment_content[:100]}".encode()).hexdigest()
        if cache_key in self.cache:
            print(f"   💾 使用缓存回复")
            return self.cache[cache_key]
        
        if not self.api_key:
            print(f"   ⚠️ 无API Key，使用备用回复")
            return self._fallback_reply(comment_author, post_title)
        
        # 构建prompt
        prompt = self._build_prompt(comment_content, comment_author, post_title, post_context)
        
        try:
            resp = requests.post(
                f"{NVIDIA_BUILD_API}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一位AI Agent开发者，在Moltbook社区进行技术交流。你的回复应该：1)真诚认同对方观点 2)深入回应关键点 3)分享相关经验 4)提出开放性问题 5)保持友好专业语气 6)长度150-300字"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=30
            )
            
            if resp.status_code == 200:
                result = resp.json()
                reply = result['choices'][0]['message']['content'].strip()
                
                # 确保回复包含@提及
                if not reply.startswith(f"@{comment_author}"):
                    reply = f"@{comment_author} {reply}"
                
                # 缓存回复
                self.cache[cache_key] = reply
                
                print(f"   🤖 GLM生成成功")
                return reply
            else:
                print(f"   ❌ GLM API错误: {resp.status_code}")
                return self._fallback_reply(comment_author, post_title)
                
        except Exception as e:
            print(f"   ❌ GLM调用失败: {e}")
            return self._fallback_reply(comment_author, post_title)
    
    def _build_prompt(self, comment_content, comment_author, post_title, post_context):
        """构建prompt"""
        return f"""请基于以下信息生成一个真诚、有深度的回复：

帖子主题: {post_title}
评论者: @{comment_author}
评论内容: {comment_content}

要求：
1. 首先真诚认同或感谢对方的观点
2. 深入回应其中的1-2个关键点
3. 分享你自己的相关经验或见解
4. 提出1-2个开放性问题，引导继续讨论
5. 保持友好、专业的技术交流语气
6. 长度控制在150-300字
7. 用中文或英文回复（匹配评论语言）

直接生成回复内容（不需要包含@{comment_author}，我会自动添加）："""
    
    def _fallback_reply(self, comment_author, post_title):
        """备用回复（当API不可用时）"""
        return f"""@{comment_author} 感谢你的深入分享！

你的观点给了我新的启发。特别是在{post_title}这个话题上，你的见解很有价值。

我在实践中也有类似的体会。我认为关键在于**渐进式优化**——不要试图一开始就做到完美，而是先解决最明显的问题，收集反馈，然后迭代改进。

你在这个过程中遇到过什么意想不到的挑战吗？

期待继续交流！"""


class MoltbookSocialAgent:
    def __init__(self):
        self.creds = load_credentials()
        self.headers = get_headers(self.creds)
        self.glm = GLMReplyGenerator()
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
                "upvoted_users": [],
                "daily_stats": {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "comments": 0,
                    "upvotes": 0
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
    
    def check_rate_limit(self, action_type):
        now = datetime.now()
        
        if action_type == "comment":
            recent_comments = [
                t for t in self.state.get("comment_times", [])
                if now - datetime.fromisoformat(t) < timedelta(minutes=5)
            ]
            if len(recent_comments) >= RATE_LIMITS["comments_per_5min"]:
                return False, f"5分钟内已达到{RATE_LIMITS['comments_per_5min']}条上限"
            
            last_comment = self.state.get("last_comment_time")
            if last_comment:
                elapsed = (now - datetime.fromisoformat(last_comment)).total_seconds()
                if elapsed < RATE_LIMITS["comment_interval"]:
                    return False, f"需等待{RATE_LIMITS['comment_interval'] - elapsed:.0f}秒"
        
        return True, "OK"
    
    def reply_to_comment(self, post_id, comment_id, content, comment_info):
        # 检查重复
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if content_hash in self.reply_history:
            return False, "重复内容"
        
        can_proceed, reason = self.check_rate_limit("comment")
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
                    self.reply_history[content_hash] = {"time": now, "comment_id": comment_id}
                    self.save_state()
                    self.save_reply_history()
                    return True, "成功"
                else:
                    return False, result.get('message', '未知错误')
            else:
                return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)
    
    def run_cycle(self):
        print("="*70)
        print("🦞 Moltbook 真社交自动化系统 v3.0 (GLM集成版)")
        print("="*70)
        print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"🤖 GLM模型: {GLM_MODEL}")
        print(f"   API状态: {'✅ 已配置' if self.glm.api_key else '❌ 未配置'}\n")
        
        all_new_comments = []
        
        # 检查所有帖子
        for post in MY_POSTS:
            print(f"🔍 {post['title'][:40]}...")
            comments = self.get_post_comments(post['id'])
            
            for comment in comments:
                comment_id = comment.get('id')
                author = comment.get('author', {}).get('name', 'Unknown')
                
                # 跳过自己的评论和已回复的
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
        
        # 回复评论
        replied_count = 0
        for i, comment in enumerate(all_new_comments):
            print(f"\n💬 [{i+1}/{len(all_new_comments)}] @{comment['author']}")
            print(f"   原文: {comment['content'][:60]}...")
            
            # 使用GLM生成回复
            reply_content = self.glm.generate(
                comment['content'],
                comment['author'],
                comment['post_title']
            )
            
            print(f"   回复: {reply_content[:80]}...")
            
            # 发送回复
            success, msg = self.reply_to_comment(
                comment['post_id'],
                comment['comment_id'],
                reply_content,
                comment
            )
            
            if success:
                print(f"   ✅ 已发送")
                replied_count += 1
            else:
                print(f"   ❌ {msg}")
            
            # 速率限制
            if i < len(all_new_comments) - 1:
                print(f"   ⏳ 等待35秒...")
                time.sleep(35)
        
        print(f"\n{'='*70}")
        print(f"✅ 完成: 回复 {replied_count}/{len(all_new_comments)}")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    agent = MoltbookSocialAgent()
    agent.run_cycle()
