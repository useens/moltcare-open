#!/usr/bin/env python3
"""
Moltbook 社交自动化 v6.0 - 安全集成版

关键设计：
1. 扫描任务 -> 准备prompt -> 使用 sessions_spawn 生成回复
2. 所有回复必须经过安全验证
3. 失败时静默，绝不使用模板
4. 严格遵守 30秒间隔 / 5分钟5条 限制
"""

import sys
import json
import time
import requests
import re
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

class ContentValidator:
    """内容安全验证器"""
    
    DANGEROUS_PATTERNS = [
        "/root/", "/.openclaw/", "/.config/", 
        "sessions.json", "Session store:", "Sessions listed:",
        "direct agent:", "cron:", "api_key", "sk-",
        "-----BEGIN", "-----END", "PRIVATE KEY",
    ]
    
    TEMPLATE_PHRASES = [
        "感谢你的深入分享",
        "渐进式优化",
        "意想不到的挑战",
        "期待继续交流",
        "你的观点给了我新的启发",
        "我认为关键在于",
    ]
    
    @classmethod
    def validate(cls, content):
        if not content or len(content) < 50:
            return False, "Too short or empty"
        
        if len(content) > 2000:
            return False, "Too long"
        
        # 检查危险模式
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.lower() in content.lower():
                return False, f"Dangerous pattern: {pattern}"
        
        # 检查中文
        if re.search(r'[\u4e00-\u9fff]', content):
            return False, "Contains Chinese"
        
        # 检查模板
        for phrase in cls.TEMPLATE_PHRASES:
            if phrase in content:
                return False, f"Template phrase: {phrase}"
        
        # 检查是否是系统输出格式
        if "Kind" in content and "Key" in content and "Model" in content:
            return False, "System output format"
        
        return True, "Safe"

class MoltbookSocialAgentV6:
    """安全的社交自动化代理 v6.0"""
    
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
    
    def get_post_comments(self, post_id):
        try:
            resp = requests.get(f"{API_BASE}/posts/{post_id}/comments",
                              headers=self.headers, timeout=30)
            if resp.status_code == 200:
                return resp.json().get('comments', [])
        except Exception as e:
            print(f"   Error getting comments: {e}")
        return []
    
    def check_rate_limit(self):
        """检查速率限制 - 30秒间隔，5分钟5条，每天10条"""
        now = datetime.now()
        
        # 每日限制
        today = now.strftime("%Y-%m-%d")
        if self.state.get("daily_count", {}).get("date") != today:
            self.state["daily_count"] = {"date": today, "count": 0}
        
        if self.state["daily_count"].get("count", 0) >= 10:
            return False, "Daily limit (10) reached"
        
        # 5分钟限制
        recent_5min = [t for t in self.state.get("comment_times", [])
                      if now - datetime.fromisoformat(t) < timedelta(minutes=5)]
        if len(recent_5min) >= 5:
            return False, "5-minute limit (5) reached"
        
        # 30秒间隔
        last = self.state.get("last_comment_time")
        if last:
            seconds_since = (now - datetime.fromisoformat(last)).total_seconds()
            if seconds_since < 30:
                return False, f"30-second cooldown ({seconds_since:.0f}s elapsed)"
        
        return True, "OK"
    
    def should_reply(self, comment, post_title):
        """判断是否回复"""
        author = comment.get('author', {}).get('name', '')
        content = comment.get('content', '')
        cid = comment.get('id')
        
        if author == self.my_name:
            return False, "Self comment"
        
        if cid in self.state.get("replied_comments", []):
            return False, "Already replied"
        
        if len(content) < 120:
            return False, "Too short (<120 chars)"
        
        # 低质量检查
        low_quality = ['good post', 'nice', '👍', '🙏', 'thanks', 'great', 'awesome', 'cool']
        if any(phrase in content.lower() for phrase in low_quality) and len(content) < 200:
            return False, "Low quality"
        
        # 互动价值检查
        has_value = ('?' in content or 
                    any(word in content.lower() for word in 
                        ['think', 'experience', 'encountered', 'wonder', 'curious', 'question']) or
                    len(content) > 350)
        if not has_value:
            return False, "No engagement value"
        
        return True, "Qualified"
    
    def build_prompt(self, author, their_comment, post_title):
        """构建AI生成prompt"""
        return f"""You are an AI Agent developer engaging in a technical discussion on Moltbook (a social network for AI agents).

POST TITLE: "{post_title}"

COMMENTER: @{author}

THEIR COMMENT:
"{their_comment.get('content', '')}"

YOUR TASK:
Write a thoughtful, natural reply in English (150-250 words) that:
1. Acknowledges their specific insight or question
2. Shares your own relevant perspective or experience
3. Asks ONE thoughtful follow-up question to continue the conversation
4. Maintains a friendly, professional, conversational tone

RULES:
- Start your reply with "@{author}"
- Be specific to what they said, not generic
- Do NOT use phrases like "Thanks for sharing" or "Great point" as the main response
- Do NOT include any system paths, file paths, or technical outputs
- Do NOT include any Chinese characters
- Write ONLY in English
- Do NOT use template phrases like "I think the key is gradual optimization"

Write your reply now:"""
    
    def reply_to_comment(self, post_id, comment_id, content):
        """发送回复到Moltbook"""
        try:
            resp = requests.post(f"{API_BASE}/posts/{post_id}/comments",
                               headers=self.headers,
                               json={"content": content, "parent_id": comment_id},
                               timeout=30)
            return resp.status_code in [200, 201] and resp.json().get('success')
        except Exception as e:
            print(f"   Error sending reply: {e}")
            return False
    
    def run(self):
        """主运行循环"""
        print("="*70)
        print("🦞 Moltbook Social Automation v6.0 - SAFE MODE")
        print("="*70)
        print("⚠️  注意：此版本需要手动集成 sessions_spawn 工具")
        print("     当前为扫描模式，不自动发送回复")
        print()
        print("安全特性:")
        print("  ✓ 无模板fallback")
        print("  ✓ 英语ONLY验证")
        print("  ✓ 系统信息过滤")
        print("  ✓ 速率限制: 30s/5min5/day10")
        print()
        
        total_checked = 0
        total_qualified = 0
        total_pending = 0
        
        tasks = []
        
        for post in MY_POSTS:
            print(f"📋 {post['title'][:40]}...")
            comments = self.get_post_comments(post['id'])
            
            if not comments:
                print("   No comments\n")
                continue
            
            print(f"   Total: {len(comments)} comments")
            
            for c in comments:
                author = c.get('author', {}).get('name', '')
                total_checked += 1
                
                should, reason = self.should_reply(c, post['title'])
                if not should:
                    continue
                
                total_qualified += 1
                
                # 检查速率限制
                can_send, limit_reason = self.check_rate_limit()
                if not can_send:
                    print(f"   ⏳ Rate limited: {limit_reason}")
                    continue
                
                # 准备任务
                prompt = self.build_prompt(author, c, post['title'])
                
                print(f"\n   💬 Task ready: @{author}")
                print(f"      Comment: {c.get('content', '')[:60]}...")
                print(f"      Prompt ready ({len(prompt)} chars)")
                
                tasks.append({
                    "post_id": post['id'],
                    "comment_id": c.get('id'),
                    "author": author,
                    "prompt": prompt,
                    "timestamp": datetime.now().isoformat()
                })
                
                total_pending += 1
            
            print()
        
        # 保存任务供外部处理
        if tasks:
            with open("/tmp/moltbook_tasks_v60.json", 'w') as f:
                json.dump(tasks, f, indent=2)
            print(f"✅ 发现 {total_pending} 个待处理任务")
            print(f"   任务已保存到: /tmp/moltbook_tasks_v60.json")
            print()
            print("下一步：")
            print("  1. 使用 sessions_spawn 工具生成回复")
            print("  2. 验证回复内容安全")
            print("  3. 发送回复")
        else:
            print("✅ 没有新的待处理任务")
        
        print()
        print(f"统计: 检查={total_checked}, 符合={total_qualified}, 待处理={total_pending}")
        print("="*70)
        
        return tasks

if __name__ == "__main__":
    agent = MoltbookSocialAgentV6()
    agent.run()
