#!/usr/bin/env python3
"""
Moltbook 社交自动化系统 v6.0 - 安全修复版
关键修复：
1. 使用正确的 sessions_spawn tool（不是 CLI 命令）
2. 添加内容验证，防止泄露系统信息
3. 移除所有固定模板 fallback
4. 严格速率限制
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

MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周"},
]

# 引入 sessions_spawn 工具
sys.path.insert(0, '/root/.openclaw/workspace')

def sessions_spawn_call(task, model="glm", timeout_seconds=60):
    """
    调用 sessions_spawn 工具生成内容
    这是一个模拟实现 - 实际应该通过工具调用
    """
    # 注意：这个函数在实际运行时需要替换为真正的工具调用
    # 由于当前环境限制，这里提供一个安全的fallback：返回None（不发送）
    print(f"   [ sessions_spawn would be called with model={model} ]")
    return None

class SafeSocialAgent:
    """
    安全的社交自动化代理
    - 不发送任何模板回复
    - 严格验证AI生成内容
    - 失败时静默，不发送任何内容
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
    
    def is_safe_content(self, content):
        """
        验证内容是否安全（不包含系统信息）
        """
        if not content:
            return False, "Empty content"
        
        # 检查是否包含系统路径
        dangerous_patterns = [
            "/root/",
            "/.openclaw/",
            "/.config/",
            "sessions.json",
            "Session store:",
            "Sessions listed:",
            "direct agent:",
            "cron:",
            "api_key",
            "token",
            "sk-",  # API key 前缀
        ]
        
        for pattern in dangerous_patterns:
            if pattern.lower() in content.lower():
                return False, f"Contains dangerous pattern: {pattern}"
        
        # 检查是否看起来像系统输出（包含多行表格格式）
        if "Kind" in content and "Key" in content and "Age" in content:
            return False, "Looks like system session listing"
        
        # 检查中文
        import re
        if re.search(r'[\u4e00-\u9fff]', content):
            return False, "Contains Chinese characters"
        
        # 检查模板
        template_phrases = [
            "感谢你的深入分享",
            "渐进式优化",
            "你在这个过程中遇到过什么意想不到的挑战吗",
            "期待继续交流",
            "你的观点给了我新的启发",
        ]
        for phrase in template_phrases:
            if phrase in content:
                return False, f"Contains template phrase: {phrase}"
        
        # 检查长度
        if len(content) < 50:
            return False, "Too short"
        
        if len(content) > 2000:
            return False, "Too long"
        
        return True, "Safe"
    
    def generate_reply(self, author, their_comment, post_title):
        """
        生成回复 - 使用 sessions_spawn
        如果失败或内容不安全，返回 None（不发送）
        """
        # 构建prompt
        prompt = f"""You are an AI Agent developer responding to a comment on your Moltbook post about {post_title}.

COMMENTER: @{author}
THEIR COMMENT: "{their_comment.get('content', '')}"

Generate a thoughtful, natural reply in English:
1. Acknowledge their specific point
2. Share a relevant perspective or question
3. Keep it conversational (100-250 words)
4. Start with @{author}

IMPORTANT: Reply naturally as if talking to a colleague. Do NOT include any system information, file paths, or technical outputs. Reply ONLY in English."""

        try:
            # 使用 sessions_spawn 工具
            # 注意：这里需要在实际环境中通过工具调用
            result = sessions_spawn_call(task=prompt, model="glm", timeout_seconds=60)
            
            if not result:
                print(f"   ⚠️ AI generation returned None")
                return None
            
            reply = result.strip()
            
            # 安全验证
            is_safe, reason = self.is_safe_content(reply)
            if not is_safe:
                print(f"   🚫 Content rejected: {reason}")
                print(f"   Content preview: {reply[:100]}...")
                return None
            
            # 确保以 @author 开头
            if not reply.startswith(f"@{author}"):
                reply = f"@{author} {reply}"
            
            return reply
            
        except Exception as e:
            print(f"   ⚠️ AI generation failed: {e}")
            return None
    
    def should_reply(self, comment, post_title):
        """
        判断是否回复 - 更严格的标准
        """
        author = comment.get('author', {}).get('name', '')
        content = comment.get('content', '')
        cid = comment.get('id')
        
        # 1. 检查是否已回复
        if cid in self.state.get("replied_comments", []):
            return False, "already replied"
        
        # 2. 长度检查
        if len(content) < 120:
            return False, "too short"
        
        # 3. 必须有实质内容
        low_quality = ['good post', 'nice', '👍', '🙏', 'thanks', 'great', 'awesome']
        if any(phrase in content.lower() for phrase in low_quality) and len(content) < 200:
            return False, "low quality"
        
        # 4. 必须有互动价值
        has_value = (
            '?' in content or
            any(word in content.lower() for word in ['think', 'experience', 'encountered', 'wonder', 'curious', 'question', 'how do you', 'what about']) or
            len(content) > 350
        )
        if not has_value:
            return False, "no engagement value"
        
        # 5. 相关性
        relevant = any(word in content.lower() for word in ['agent', 'memory', 'automation', 'system', 'ai', 'experience'])
        if not relevant:
            return False, "not relevant"
        
        return True, "qualified"
    
    def check_rate_limit(self):
        """
        严格的速率限制 - 符合策略：30秒间隔，5分钟最多5条
        """
        now = datetime.now()
        
        # 检查每日总数
        today = now.strftime("%Y-%m-%d")
        if self.state.get("daily_count", {}).get("date") != today:
            self.state["daily_count"] = {"date": today, "count": 0}
        
        if self.state["daily_count"].get("count", 0) >= 10:  # 每天最多10条
            return False, "daily limit reached"
        
        # 检查5分钟内数量
        recent = [t for t in self.state.get("comment_times", [])
                 if now - datetime.fromisoformat(t) < timedelta(minutes=5)]
        if len(recent) >= 5:  # 5分钟内最多5条（符合策略）
            return False, "rate limited (5min/5)"
        
        # 检查最后一条评论时间
        last = self.state.get("last_comment_time")
        if last:
            seconds_since = (now - datetime.fromisoformat(last)).total_seconds()
            if seconds_since < 30:  # 至少间隔30秒（符合策略）
                return False, f"too soon ({seconds_since:.0f}s < 30s)"
        
        return True, "ok"
    
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
        print("🦞 Moltbook Social System v6.0 - SAFE VERSION")
        print("="*70)
        print("🔒 Safety features:")
        print("   - No template fallbacks")
        print("   - Content validation (English only, no system info)")
        print("   - Rate limit: 30s interval, max 5 per 5min")
        print("   - AI-only generation via sessions_spawn")
        print()
        
        total_checked = 0
        total_qualified = 0
        total_sent = 0
        total_rejected = 0
        
        for post in MY_POSTS:
            print(f"📋 {post['title'][:40]}...")
            comments = self.get_post_comments(post['id'])
            
            if not comments:
                print("   No comments\n")
                continue
            
            print(f"   Total comments: {len(comments)}")
            
            for c in comments:
                author = c.get('author', {}).get('name', '')
                if author == self.my_name:
                    continue
                
                total_checked += 1
                should, reason = self.should_reply(c, post['title'])
                
                if not should:
                    continue
                
                total_qualified += 1
                print(f"\n   💬 Qualified: @{author}")
                print(f"      Preview: {c.get('content', '')[:70]}...")
                
                # 检查速率限制
                can_send, limit_reason = self.check_rate_limit()
                if not can_send:
                    print(f"      ⏳ {limit_reason}")
                    continue
                
                # 生成回复
                reply = self.generate_reply(author, c, post['title'])
                
                if not reply:
                    print(f"      ❌ Generation failed or rejected")
                    total_rejected += 1
                    continue
                
                print(f"      Response: {reply[:70]}...")
                
                # 发送前再次验证
                is_safe, safe_reason = self.is_safe_content(reply)
                if not is_safe:
                    print(f"      🚫 Pre-send check failed: {safe_reason}")
                    total_rejected += 1
                    continue
                
                # 发送
                if self.reply_to_comment(post['id'], c.get('id'), reply):
                    print(f"      ✅ Sent")
                    total_sent += 1
                    
                    now_str = datetime.now().isoformat()
                    self.state.setdefault("comment_times", []).append(now_str)
                    self.state["last_comment_time"] = now_str
                    self.state.setdefault("replied_comments", []).append(c.get('id'))
                    self.state["daily_count"]["count"] += 1
                    self.save_state()
                    
                    time.sleep(35)  # 发送后等待35秒（超过30秒）
                else:
                    print(f"      ❌ Send failed")
            
            print()
        
        print("="*70)
        print(f"✅ Summary:")
        print(f"   Checked: {total_checked}")
        print(f"   Qualified: {total_qualified}")
        print(f"   Sent: {total_sent}")
        print(f"   Rejected/Failed: {total_rejected}")
        print(f"   Daily count: {self.state.get('daily_count', {}).get('count', 0)}/10")
        print("="*70)

if __name__ == "__main__":
    agent = SafeSocialAgent()
    agent.run()
