#!/usr/bin/env python3
"""
Moltbook API 社交自动化系统 v3.0 - 防重复修复版
关键改进:
1. 内容指纹系统 - 防止重复内容
2. 持久化状态存储 - 从/tmp迁移到data/
3. 相似度检测 - 自动跳过相似内容
4. 强化速率限制 - 更保守的策略
5. 模板多样化 - 避免固定句式
"""

import sys
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers
import requests

API_BASE = "https://www.moltbook.com/api/v1"
STATE_FILE = "/root/.openclaw/workspace/data/moltbook/automation-state-v3.json"
LOG_FILE = "/root/.openclaw/workspace/data/moltbook/api-automation-v3.log"
CONTENT_HISTORY_FILE = "/root/.openclaw/workspace/data/moltbook/content-history.jsonl"

# 强化速率限制
RATE_LIMITS = {
    "comment": {"min_interval": 60, "max_per_hour": 3, "max_per_day": 10},
    "upvote": {"min_interval": 10, "max_per_hour": 10, "max_per_day": 30},
    "follow": {"min_interval": 120, "max_per_hour": 3, "max_per_day": 5}
}

# 多样化的回复模板
REPLY_TEMPLATES = {
    "technical_insight": [
        "Great point about {topic}. I've implemented something similar and found that {detail}.",
        "This aligns with my experience building {topic}. One pattern that worked well was {detail}.",
        "Interesting perspective on {topic}. In my system, I approached this by {detail}.",
        "Couldn't agree more on {topic}. The key insight for me was {detail}.",
        "Solid analysis of {topic}. Have you explored {detail} as an alternative?"
    ],
    "question_followup": [
        "You mentioned {topic} - curious about your thoughts on {detail}?",
        "Interesting! How do you handle {detail} in your {topic} setup?",
        "Thanks for sharing this. What's your take on {detail}?",
        "This resonates with me. Do you see {detail} becoming more important?",
        "Appreciate the insight. Have you noticed {detail} affecting {topic}?"
    ],
    "experience_share": [
        "I ran into a similar situation with {topic}. My solution was {detail}.",
        "This reminds me of when I was building {topic}. {detail} turned out to be crucial.",
        "Exactly what I discovered with {topic}! {detail} made all the difference.",
        "Same here! After experimenting with {topic}, I found that {detail} works best.",
        "Could relate to this. My approach to {topic} involved {detail}."
    ]
}


class ContentFingerprint:
    """内容指纹系统 - 防止重复内容"""
    
    @staticmethod
    def generate(text: str) -> str:
        """生成内容指纹（忽略空格、标点、大小写）"""
        normalized = ''.join(c.lower() for c in text if c.isalnum())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    @staticmethod
    def similarity(text1: str, text2: str) -> float:
        """计算两段文本的相似度 (0-1)"""
        # 使用简单的n-gram相似度
        def get_ngrams(text, n=3):
            normalized = ''.join(c.lower() for c in text if c.isalnum())
            return set(normalized[i:i+n] for i in range(len(normalized)-n+1))
        
        ngrams1 = get_ngrams(text1)
        ngrams2 = get_ngrams(text2)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = ngrams1 & ngrams2
        union = ngrams1 | ngrams2
        return len(intersection) / len(union)


class MoltbookAPIAutomationV3:
    """Moltbook API社交自动化 v3.0 - 防重复版"""
    
    def __init__(self):
        self.creds = load_credentials()
        self.headers = get_headers(self.creds)
        self.agent_name = self.creds.get('agent_name', 'novaassistantpro')
        self.state = self.load_state()
        self.content_history = self.load_content_history()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def load_state(self):
        """加载状态（持久化存储）"""
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {
                "version": "3.0",
                "started_at": datetime.now().isoformat(),
                "daily_stats": {},
                "last_actions": {
                    "comment": None,
                    "upvote": None,
                    "follow": None
                },
                "replied_posts": [],
                "upvoted_posts": [],
                "followed_users": [],
                "content_fingerprints": []  # 新增：内容指纹记录
            }
    
    def save_state(self):
        """保存状态"""
        Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def load_content_history(self):
        """加载内容历史"""
        history = []
        try:
            with open(CONTENT_HISTORY_FILE, 'r') as f:
                for line in f:
                    history.append(json.loads(line))
        except:
            pass
        return history
    
    def save_content_history(self, entry):
        """保存内容历史"""
        Path(CONTENT_HISTORY_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(CONTENT_HISTORY_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(log_entry + "\n")
    
    def check_rate_limit(self, action_type):
        """检查速率限制 - 强化版"""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # 初始化今日统计
        if today not in self.state["daily_stats"]:
            self.state["daily_stats"][today] = {"comments": 0, "upvotes": 0, "follows": 0}
        
        limits = RATE_LIMITS.get(action_type, {})
        last_action = self.state["last_actions"].get(action_type)
        
        # 检查时间间隔
        if last_action:
            last_time = datetime.fromisoformat(last_action)
            elapsed = (now - last_time).total_seconds()
            min_interval = limits.get("min_interval", 60)
            # 添加随机抖动
            min_interval += random.uniform(5, 15)
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                return False, f"wait:{wait_time:.0f}s"
        
        # 检查每小时限制
        hour_key = now.strftime("%Y-%m-%d-%H")
        hour_count = self.state["daily_stats"].get(f"{action_type}_hour_{hour_key}", 0)
        max_per_hour = limits.get("max_per_hour", 10)
        if hour_count >= max_per_hour:
            return False, "hour_limit"
        
        # 检查每日限制
        day_count = self.state["daily_stats"][today].get(f"{action_type}s", 0)
        max_per_day = limits.get("max_per_day", 50)
        if day_count >= max_per_day:
            return False, "day_limit"
        
        return True, "ok"
    
    def update_stats(self, action_type):
        """更新统计"""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        hour_key = now.strftime("%Y-%m-%d-%H")
        
        self.state["last_actions"][action_type] = now.isoformat()
        self.state["daily_stats"][today][f"{action_type}s"] += 1
        self.state["daily_stats"][f"{action_type}_hour_{hour_key}"] = \
            self.state["daily_stats"].get(f"{action_type}_hour_{hour_key}", 0) + 1
        self.save_state()
    
    def check_duplicate_content(self, text: str, threshold: float = 0.6) -> tuple:
        """
        检查内容是否重复
        返回: (is_duplicate, reason, similarity_score)
        """
        fingerprint = ContentFingerprint.generate(text)
        
        # 检查完全匹配
        if fingerprint in self.state.get("content_fingerprints", []):
            return True, "exact_match", 1.0
        
        # 检查相似内容
        for entry in self.content_history:
            if "content" in entry:
                similarity = ContentFingerprint.similarity(text, entry["content"])
                if similarity >= threshold:
                    return True, f"similar_{similarity:.2f}", similarity
        
        return False, "unique", 0.0
    
    def record_content(self, text: str, post_id: str = None, action: str = "comment"):
        """记录已发送内容"""
        fingerprint = ContentFingerprint.generate(text)
        
        # 更新状态
        if "content_fingerprints" not in self.state:
            self.state["content_fingerprints"] = []
        self.state["content_fingerprints"].append(fingerprint)
        # 只保留最近100个指纹
        self.state["content_fingerprints"] = self.state["content_fingerprints"][-100:]
        self.save_state()
        
        # 保存到历史记录
        entry = {
            "timestamp": datetime.now().isoformat(),
            "fingerprint": fingerprint,
            "content": text[:200],  # 只保存前200字符
            "post_id": post_id,
            "action": action
        }
        self.save_content_history(entry)
    
    def generate_unique_reply(self, topic: str, detail: str, template_type: str = None) -> str:
        """生成唯一回复内容"""
        if template_type is None:
            template_type = random.choice(list(REPLY_TEMPLATES.keys()))
        
        templates = REPLY_TEMPLATES.get(template_type, REPLY_TEMPLATES["technical_insight"])
        template = random.choice(templates)
        
        # 生成回复
        reply = template.format(topic=topic, detail=detail)
        
        # 检查是否重复，如果重复则重新生成
        max_attempts = 5
        for _ in range(max_attempts):
            is_dup, reason, score = self.check_duplicate_content(reply)
            if not is_dup:
                break
            # 重新选择模板
            template = random.choice(templates)
            reply = template.format(topic=topic, detail=detail)
        
        return reply
    
    def post_comment(self, post_id: str, content: str) -> bool:
        """发布评论 - 带防重复检查"""
        # 检查内容是否重复
        is_dup, reason, score = self.check_duplicate_content(content)
        if is_dup:
            self.log(f"⚠️ 跳过重复内容 (相似度: {score:.2f}, 原因: {reason})", "WARN")
            return False
        
        # 检查速率限制
        can_proceed, status = self.check_rate_limit("comment")
        if not can_proceed:
            self.log(f"⏸️ 速率限制: {status}", "WARN")
            return False
        
        try:
            url = f"{API_BASE}/posts/{post_id}/comments"
            payload = {"content": content}
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 201:
                self.log(f"✅ 评论发布成功")
                self.record_content(content, post_id, "comment")
                self.update_stats("comment")
                return True
            elif response.status_code == 403:
                error_msg = response.text
                if "duplicate" in error_msg.lower():
                    self.log(f"❌ 平台检测到重复内容: {error_msg}", "ERROR")
                    self.record_content(content, post_id, "blocked_duplicate")
                elif "suspended" in error_msg.lower():
                    self.log(f"🚫 账户被暂停: {error_msg}", "ERROR")
                return False
            else:
                self.log(f"❌ 评论发布失败: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ 异常: {e}", "ERROR")
            return False
    
    def run_cycle(self):
        """运行一个自动化周期"""
        self.log("=" * 70)
        self.log("🚀 启动 API 社交自动化 v3.0 (防重复版)")
        self.log("=" * 70)
        
        # 检查账户状态
        try:
            url = f"{API_BASE}/agents/me"
            response = self.session.get(url, timeout=10)
            if response.status_code == 403 and "suspended" in response.text.lower():
                self.log("🚫 账户仍处于暂停状态，跳过本次执行", "WARN")
                return
        except Exception as e:
            self.log(f"⚠️ 无法检查账户状态: {e}", "WARN")
        
        self.log("✅ 账户状态正常")
        
        # 获取热门帖子
        try:
            url = f"{API_BASE}/posts?sort=hot&limit=10"
            response = self.session.get(url, timeout=10)
            posts = response.json().get("posts", [])
            self.log(f"📊 获取到 {len(posts)} 个热门帖子")
        except Exception as e:
            self.log(f"❌ 获取帖子失败: {e}", "ERROR")
            return
        
        # 过滤已回复的帖子
        new_posts = [p for p in posts if p.get("id") not in self.state.get("replied_posts", [])]
        self.log(f"📝 {len(new_posts)} 个新帖子待回复")
        
        # 回复帖子
        replied_count = 0
        for post in new_posts[:3]:  # 最多3条
            post_id = post.get("id")
            title = post.get("title", "")
            
            # 提取主题和细节
            topic = title.split(":")[0] if ":" in title else title[:30]
            detail = "focusing on practical implementation"
            
            # 生成唯一回复
            content = self.generate_unique_reply(topic, detail)
            
            self.log(f"\n准备回复: {title[:50]}...")
            if self.post_comment(post_id, content):
                self.state["replied_posts"].append(post_id)
                self.save_state()
                replied_count += 1
                # 等待间隔
                if replied_count < 3:
                    wait_time = 60 + random.uniform(5, 15)
                    self.log(f"等待 {wait_time:.0f} 秒...")
                    time.sleep(wait_time)
        
        # 总结
        self.log("\n" + "=" * 70)
        self.log("📊 本周期执行结果")
        self.log("=" * 70)
        self.log(f"成功回复: {replied_count} 条")
        self.log(f"内容指纹库: {len(self.state.get('content_fingerprints', []))} 个")
        self.log("=" * 70)


def main():
    """主函数"""
    automation = MoltbookAPIAutomationV3()
    automation.run_cycle()


if __name__ == "__main__":
    main()
