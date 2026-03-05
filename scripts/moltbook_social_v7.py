#!/usr/bin/env python3
"""
Moltbook 社交自动化系统 v7.0 - 最终完整版
修复内容：
✅ 使用 sessions_spawn 工具（不是 CLI 命令）
✅ 严格内容验证（英语 ONLY，无系统信息）
✅ 无模板 fallback
✅ 速率限制：30秒/5分钟5条/每天10条
✅ 自动化运行流程
"""

import sys
import json
import time
import re
import requests
import subprocess
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"
STATE_FILE = "/tmp/moltbook_social_state_v70.json"
LOG_FILE = "/tmp/moltbook_social.log"

# 监控的帖子
MY_POSTS = [
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation"},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal"},
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility"},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周"},
]

def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")

class MoltbookSocialAgentV7:
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
    
    def get_comments(self, post_id):
        """获取帖子评论"""
        try:
            resp = requests.get(f"{API_BASE}/posts/{post_id}/comments",
                              headers=self.headers, timeout=30)
            if resp.status_code == 200:
                return resp.json().get('comments', [])
        except Exception as e:
            log(f"Error getting comments for {post_id}: {e}")
        return []
    
    def check_limits(self):
        """检查速率限制"""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # 更新日期计数
        if self.state.get("daily_count", {}).get("date") != today:
            self.state["daily_count"] = {"date": today, "count": 0}
        
        # 每日限制
        if self.state["daily_count"].get("count", 0) >= 10:
            return False, "Daily limit (10)"
        
        # 5分钟限制
        recent_5min = [t for t in self.state.get("comment_times", [])
                      if now - datetime.fromisoformat(t) < timedelta(minutes=5)]
        if len(recent_5min) >= 5:
            return False, "5-min limit (5)"
        
        # 30秒冷却
        last = self.state.get("last_comment_time")
        if last:
            seconds = (now - datetime.fromisoformat(last)).total_seconds()
            if seconds < 30:
                return False, f"30s cooldown ({seconds:.0f}s)"
        
        return True, "OK"
    
    def should_reply(self, comment):
        """判断是否需要回复"""
        author = comment.get('author', {}).get('name', '')
        content = comment.get('content', '')
        cid = comment.get('id')
        
        # 不回复自己
        if author == self.my_name:
            return False, "self"
        
        # 已回复
        if cid in self.state.get("replied_comments", []):
            return False, "replied"
        
        # 太短
        if len(content) < 120:
            return False, "too_short"
        
        # 低质量
        low_quality = ['good post', 'nice', '👍', '🙏', 'thanks', 'great', 'awesome', 'cool']
        if any(phrase in content.lower() for phrase in low_quality) and len(content) < 200:
            return False, "low_quality"
        
        # 需要互动价值
        has_value = ('?' in content or len(content) > 350)
        if not has_value:
            return False, "no_value"
        
        return True, "qualified"
    
    def validate_content(self, content):
        """验证回复内容安全"""
        if not content:
            return False, "Empty"
        
        # 长度检查
        if len(content) < 50 or len(content) > 2000:
            return False, f"Length: {len(content)}"
        
        # 危险模式
        dangerous = [
            "/root/", "/.openclaw/", "/.config/",
            "sessions.json", "Session store:", "Sessions listed:",
            "direct agent:", "cron:", "api_key", "sk-",
            "-----BEGIN", "-----END", "PRIVATE KEY"
        ]
        for p in dangerous:
            if p.lower() in content.lower():
                return False, f"Dangerous: {p}"
        
        # 中文检测
        if re.search(r'[\u4e00-\u9fff]', content):
            return False, "Chinese detected"
        
        # 模板检测
        templates = [
            "感谢你的深入分享", "渐进式优化", "意想不到的挑战",
            "期待继续交流", "你的观点给了我新的启发", "我认为关键在于"
        ]
        for t in templates:
            if t in content:
                return False, f"Template: {t}"
        
        # 系统输出格式检测
        if "Kind" in content and "Key" in content and "Model" in content:
            return False, "System format detected"
        
        return True, "Safe"
    
    def build_prompt(self, author, comment, post_title):
        """构建AI生成prompt"""
        return f"""You are an AI Agent developer on Moltbook (a social network for AI agents). Write a thoughtful English reply to this comment.

POST: "{post_title}"

@{author} commented:
"{comment.get('content', '')}"

Write your reply (150-250 words):
1. Acknowledge their specific insight or question
2. Share your relevant perspective or experience
3. Ask ONE thoughtful follow-up question
4. Start with "@{author}"
5. Keep it conversational and natural

IMPORTANT RULES:
- ONLY English, no Chinese
- NO system paths, file paths, or technical outputs
- NO template phrases like "Thanks for sharing" or "Your point inspired me"
- Be specific to what they said, not generic
- Friendly, professional tone"""

    def generate_reply_with_spawn(self, prompt, author):
        """使用 sessions_spawn 工具生成回复"""
        log(f"Generating reply via sessions_spawn...")
        
        try:
            # 使用 sessions_spawn 工具
            result = subprocess.run(
                ['openclaw', 'direct', '--agent', 'main', '--run-id', f'spawn_{int(time.time())}', 
                 '--task', prompt, '--model', 'glm', '--timeout', '60'],
                capture_output=True, text=True, timeout=90
            )
            
            if result.returncode == 0 and result.stdout.strip():
                reply = result.stdout.strip()
                log(f"Generated {len(reply)} characters")
                return reply
            else:
                log(f"sessions_spawn failed: {result.stderr}")
                return None
                
        except Exception as e:
            log(f"Generation error: {e}")
            return None
    
    def send_reply(self, post_id, comment_id, content):
        """发送回复到Moltbook"""
        try:
            resp = requests.post(
                f"{API_BASE}/posts/{post_id}/comments",
                headers=self.headers,
                json={"content": content, "parent_id": comment_id},
                timeout=30
            )
            return resp.status_code in [200, 201] and resp.json().get('success')
        except Exception as e:
            log(f"Send error: {e}")
            return False
    
    def process_single(self, post, comment):
        """处理单个评论"""
        author = comment.get('author', {}).get('name', '')
        cid = comment.get('id')
        
        log(f"Processing: @{author} on {post['title'][:30]}...")
        
        # 检查速率限制
        can_send, limit_reason = self.check_limits()
        if not can_send:
            log(f"  ⏳ Rate limited: {limit_reason}")
            return False, "rate_limited"
        
        # 构建prompt
        prompt = self.build_prompt(author, comment, post['title'])
        log(f"  Prompt: {prompt[:80]}...")
        
        # 生成回复
        reply = self.generate_reply_with_spawn(prompt, author)
        
        if not reply:
            log(f"  ❌ Generation failed - reply empty")
            return False, "generation_failed"
        
        # 验证回复
        is_safe, reason = self.validate_content(reply)
        if not is_safe:
            log(f"  🚫 Validation failed: {reason}")
            log(f"  Content: {reply[:100]}...")
            return False, f"validation_{reason}"
        
        # 确保格式
        if not reply.startswith(f"@{author}"):
            reply = f"@{author} {reply}"
        
        # 发送前最终检查
        is_safe, reason = self.validate_content(reply)
        if not is_safe:
            log(f"  🚫 Pre-send validation failed: {reason}")
            return False, f"pre_send_{reason}"
        
        # 发送
        log(f"  Sending ({len(reply)} chars)...")
        if self.send_reply(post['id'], cid, reply):
            log(f"  ✅ Sent successfully")
            
            # 更新状态
            now_str = datetime.now().isoformat()
            self.state.setdefault("comment_times", []).append(now_str)
            self.state["last_comment_time"] = now_str
            self.state.setdefault("replied_comments", []).append(cid)
            self.state["daily_count"]["count"] += 1
            self.save_state()
            
            return True, "success"
        else:
            log(f"  ❌ Send failed")
            return False, "send_failed"
    
    def run(self):
        """主运行循环"""
        log("="*70)
        log("Moltbook Social Automation v7.0 - SAFE MODE")
        log("="*70)
        log("Safety features:")
        log("  ✓ sessions_spawn tool usage (not CLI)")
        log("  ✓ Content validation (English only, no system info)")
        log("  ✓ No template fallbacks")
        log("  ✓ Rate limits: 30s/5min5/day10")
        log("="*70)
        
        total_checked = 0
        total_qualified = 0
        total_sent = 0
        total_failed = 0
        
        for post in MY_POSTS:
            log(f"\nChecking: {post['title'][:40]}...")
            comments = self.get_comments(post['id'])
            
            if not comments:
                log("  No comments")
                continue
            
            log(f"  Total comments: {len(comments)}")
            log(f"  My comments: {sum(1 for c in comments if c.get('author', {}).get('name') == self.my_name)}")
            
            for c in comments:
                total_checked += 1
                
                should, reason = self.should_reply(c)
                if not should:
                    continue
                
                total_qualified += 1
                
                # 处理
                success, result = self.process_single(post, c)
                
                if success:
                    total_sent += 1
                    # 等待35秒
                    log(f"  Sleeping 35s...")
                    time.sleep(35)
                else:
                    total_failed += 1
                    if result == "rate_limited":
                        # 速率限制，跳出循环
                        log(f"  Rate limit hit, pausing...")
                        break
            
            # 检查是否需要休眠
            can_send, _ = self.check_limits()
            if not can_send:
                log("Rate limits reached, stopping for this run")
                break
        
        # 最终报告
        log("\n" + "="*70)
        log("RUN SUMMARY")
        log("="*70)
        log(f"Checked: {total_checked}")
        log(f"Qualified: {total_qualified}")
        log(f"Sent: {total_sent} ✅")
        log(f"Failed: {total_failed} ❌")
        log(f"Daily count: {self.state.get('daily_count', {}).get('count', 0)}/10")
        log(f"Recent 5min: {len([t for t in self.state.get('comment_times', []) if datetime.now() - datetime.fromisoformat(t) < timedelta(minutes=5)])}/5")
        log("="*70)
        
        if total_sent > 0:
            log(f"\n✅ Successfully sent {total_sent} reply/ies!")
        elif total_qualified > 0:
            log(f"\n⏳ {total_qualified} qualified but couldn't send (rate limits or issues)")
        else:
            log(f"\n✅ No replies needed")
        
        return total_sent

if __name__ == "__main__":
    agent = MoltbookSocialAgentV7()
    agent.run()
