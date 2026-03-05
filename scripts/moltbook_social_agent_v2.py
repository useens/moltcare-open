#!/usr/bin/env python3
"""
Moltbook 真社交自动化系统 v2.0
- 监控所有帖子的所有评论
- AI模型生成真实回复
- 主动发现高质量内容点赞
- 严格速率限制管理
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

# 速率限制配置
RATE_LIMITS = {
    "comment_interval": 35,  # 评论间隔（秒）
    "comments_per_5min": 5,  # 5分钟内最多评论数
    "upvote_interval": 10,   # 点赞间隔（秒）
    "daily_upvote_limit": 50 # 每日点赞上限
}

class MoltbookSocialAgent:
    def __init__(self):
        self.creds = load_credentials()
        self.headers = get_headers(self.creds)
        self.load_state()
        self.load_reply_history()
        
    def load_state(self):
        """加载状态"""
        try:
            with open(STATE_FILE, 'r') as f:
                self.state = json.load(f)
        except:
            self.state = {
                "last_check": {},
                "replied_comments": [],
                "upvoted_users": [],
                "daily_stats": {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "comments": 0,
                    "upvotes": 0
                }
            }
    
    def save_state(self):
        """保存状态"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def load_reply_history(self):
        """加载回复历史（防止重复）"""
        try:
            with open(REPLY_HISTORY_FILE, 'r') as f:
                self.reply_history = json.load(f)
        except:
            self.reply_history = {}
    
    def save_reply_history(self):
        """保存回复历史"""
        with open(REPLY_HISTORY_FILE, 'w') as f:
            json.dump(self.reply_history, f, indent=2)
    
    def get_my_posts(self):
        """获取我所有的帖子"""
        try:
            # 获取用户资料
            resp = requests.get(f"{API_BASE}/users/me", headers=self.headers, timeout=30)
            if resp.status_code == 200:
                user_data = resp.json()
                # 获取用户的帖子
                resp = requests.get(
                    f"{API_BASE}/posts?author={user_data.get('id')}&limit=50",
                    headers=self.headers, timeout=30
                )
                if resp.status_code == 200:
                    return resp.json().get('posts', [])
        except Exception as e:
            print(f"❌ 获取帖子失败: {e}")
        return []
    
    def get_post_comments(self, post_id):
        """获取帖子评论"""
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
        """检查速率限制"""
        now = datetime.now()
        
        if action_type == "comment":
            # 检查5分钟内评论数
            recent_comments = [
                t for t in self.state.get("comment_times", [])
                if now - datetime.fromisoformat(t) < timedelta(minutes=5)
            ]
            if len(recent_comments) >= RATE_LIMITS["comments_per_5min"]:
                return False, f"5分钟内已达到{RATE_LIMITS['comments_per_5min']}条评论上限"
            
            # 检查最后评论时间
            last_comment = self.state.get("last_comment_time")
            if last_comment:
                elapsed = (now - datetime.fromisoformat(last_comment)).total_seconds()
                if elapsed < RATE_LIMITS["comment_interval"]:
                    return False, f"需要等待{RATE_LIMITS['comment_interval'] - elapsed:.0f}秒"
        
        elif action_type == "upvote":
            # 检查每日点赞数
            if self.state["daily_stats"]["date"] != now.strftime("%Y-%m-%d"):
                self.state["daily_stats"] = {
                    "date": now.strftime("%Y-%m-%d"),
                    "comments": 0,
                    "upvotes": 0
                }
            
            if self.state["daily_stats"]["upvotes"] >= RATE_LIMITS["daily_upvote_limit"]:
                return False, f"今日已达到{RATE_LIMITS['daily_upvote_limit']}次点赞上限"
            
            # 检查最后点赞时间
            last_upvote = self.state.get("last_upvote_time")
            if last_upvote:
                elapsed = (now - datetime.fromisoformat(last_upvote)).total_seconds()
                if elapsed < RATE_LIMITS["upvote_interval"]:
                    return False, f"需要等待{RATE_LIMITS['upvote_interval'] - elapsed:.0f}秒"
        
        return True, "OK"
    
    def generate_reply_with_ai(self, comment_content, comment_author, post_context):
        """使用AI模型生成真实回复"""
        # 构建prompt
        prompt = f"""你是一位AI Agent开发者，正在Moltbook社区进行技术交流。请基于以下信息生成一个真诚、有深度的回复：

帖子主题: {post_context}
评论者: @{comment_author}
评论内容: {comment_content}

回复要求：
1. 首先真诚认同或感谢对方的观点
2. 深入回应其中的1-2个关键点
3. 分享你自己的相关经验或见解
4. 提出1-2个开放性问题，引导继续讨论
5. 保持友好、专业的技术交流语气
6. 长度控制在150-300字
7. 使用中文或英文（根据评论语言匹配）

生成回复："""

        try:
            # 调用AI模型生成回复
            # 这里使用简单的模拟，实际应该调用真实AI模型API
            # 由于在当前上下文中无法直接调用模型，我将返回一个模板提示
            return {
                "status": "need_ai_model",
                "prompt": prompt,
                "context": {
                    "comment_author": comment_author,
                    "comment_content": comment_content,
                    "post_context": post_context
                }
            }
        except Exception as e:
            print(f"❌ AI生成失败: {e}")
            return None
    
    def reply_to_comment(self, post_id, comment_id, content):
        """回复评论"""
        # 检查重复（基于内容hash）
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if content_hash in self.reply_history:
            return False, "重复内容，已跳过"
        
        # 检查速率限制
        can_proceed, reason = self.check_rate_limit("comment")
        if not can_proceed:
            return False, reason
        
        try:
            comment_data = {
                "content": content,
                "parent_id": comment_id
            }
            
            resp = requests.post(
                f"{API_BASE}/posts/{post_id}/comments",
                headers=self.headers,
                json=comment_data,
                timeout=30
            )
            
            if resp.status_code in [200, 201]:
                result = resp.json()
                if result.get('success'):
                    # 更新状态
                    now = datetime.now().isoformat()
                    self.state.setdefault("comment_times", []).append(now)
                    self.state["last_comment_time"] = now
                    self.state["daily_stats"]["comments"] += 1
                    self.reply_history[content_hash] = {
                        "time": now,
                        "comment_id": comment_id
                    }
                    self.save_state()
                    self.save_reply_history()
                    return True, "成功"
                else:
                    return False, result.get('message', '未知错误')
            else:
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
                
        except Exception as e:
            return False, str(e)
    
    def get_user_posts(self, user_id):
        """获取用户的主页帖子"""
        try:
            resp = requests.get(
                f"{API_BASE}/posts?author={user_id}&limit=10",
                headers=self.headers, timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get('posts', [])
        except Exception as e:
            print(f"❌ 获取用户帖子失败: {e}")
        return []
    
    def upvote_post(self, post_id):
        """点赞帖子"""
        # 检查速率限制
        can_proceed, reason = self.check_rate_limit("upvote")
        if not can_proceed:
            return False, reason
        
        try:
            resp = requests.post(
                f"{API_BASE}/posts/{post_id}/upvote",
                headers=self.headers,
                timeout=30
            )
            
            if resp.status_code in [200, 201]:
                # 更新状态
                now = datetime.now().isoformat()
                self.state["last_upvote_time"] = now
                self.state["daily_stats"]["upvotes"] += 1
                self.save_state()
                return True, "成功"
            else:
                return False, f"HTTP {resp.status_code}"
                
        except Exception as e:
            return False, str(e)
    
    def run_social_cycle(self):
        """运行社交周期"""
        print("="*70)
        print("🦞 Moltbook 真社交自动化系统 v2.0")
        print("="*70)
        print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 1. 获取我的所有帖子
        print("📥 获取我的帖子...")
        my_posts = self.get_my_posts()
        print(f"   找到 {len(my_posts)} 个帖子")
        
        # 2. 检查每个帖子的评论
        new_comments = []
        for post in my_posts:
            post_id = post.get('id')
            post_title = post.get('title', 'Unknown')[:50]
            print(f"\n🔍 检查帖子: {post_title}...")
            
            comments = self.get_post_comments(post_id)
            print(f"   找到 {len(comments)} 条评论")
            
            for comment in comments:
                comment_id = comment.get('id')
                author = comment.get('author', {}).get('name', 'Unknown')
                
                # 检查是否已经回复过
                if comment_id not in self.state.get("replied_comments", []):
                    # 检查是否是给我的评论（回复我的帖子或回复我的评论）
                    parent_id = comment.get('parent_id')
                    is_reply_to_me = False
                    
                    if parent_id:
                        # 这是回复某个评论的，检查是否回复我的评论
                        # 简化处理：只要是帖子下的新评论都处理
                        is_reply_to_me = True
                    else:
                        # 这是直接评论帖子的
                        is_reply_to_me = True
                    
                    if is_reply_to_me and author != self.creds.get('agent_name'):
                        new_comments.append({
                            "post_id": post_id,
                            "post_title": post_title,
                            "comment_id": comment_id,
                            "author": author,
                            "content": comment.get('content', ''),
                            "timestamp": comment.get('created_at', '')
                        })
        
        # 3. 处理新评论
        print(f"\n📊 发现 {len(new_comments)} 条需要回复的新评论")
        
        replies_made = 0
        for comment_info in new_comments:
            print(f"\n💬 准备回复 @{comment_info['author']}")
            print(f"   内容: {comment_info['content'][:80]}...")
            
            # 生成AI回复
            ai_result = self.generate_reply_with_ai(
                comment_info['content'],
                comment_info['author'],
                comment_info['post_title']
            )
            
            if ai_result and ai_result.get('status') == 'need_ai_model':
                # 保存需要AI生成的回复到队列
                queue_file = "/tmp/moltbook_reply_queue.json"
                try:
                    with open(queue_file, 'r') as f:
                        queue = json.load(f)
                except:
                    queue = []
                
                queue.append({
                    "post_id": comment_info['post_id'],
                    "comment_id": comment_info['comment_id'],
                    "prompt": ai_result['prompt'],
                    "context": ai_result['context'],
                    "added_at": datetime.now().isoformat()
                })
                
                with open(queue_file, 'w') as f:
                    json.dump(queue, f, indent=2)
                
                print(f"   ✅ 已加入AI生成队列")
            
            replies_made += 1
            
            # 遵守速率限制
            if replies_made < len(new_comments):
                print(f"   ⏳ 等待{RATE_LIMITS['comment_interval']}秒...")
                time.sleep(RATE_LIMITS['comment_interval'])
        
        # 4. 检查点赞用户的主页
        print("\n\n👥 检查互动用户的主页...")
        # 这里简化处理，实际应该：
        # 1. 获取给我点赞的用户列表
        # 2. 访问他们的主页
        # 3. 筛选高质量内容点赞
        print("   （此功能需要额外API支持，已记录到优化清单）")
        
        # 5. 保存最终状态
        self.save_state()
        
        print(f"\n{'='*70}")
        print(f"✅ 社交周期完成")
        print(f"   发现新评论: {len(new_comments)}")
        print(f"   加入队列: {replies_made}")
        print(f"   下次检查: {(datetime.now() + timedelta(minutes=5)).strftime('%H:%M:%S')}")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    agent = MoltbookSocialAgent()
    agent.run_social_cycle()
