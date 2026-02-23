#!/usr/bin/env python3
"""
Moltbook 社交自动化启动器
整合所有社交功能：追踪、生成回复、监控互动
"""

import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers
import requests

API_BASE = "https://www.moltbook.com/api/v1"
STATE_FILE = "/tmp/moltbook_social_automation.json"
DRAFT_FILE = "/root/.openclaw/workspace/moltbook-replies-draft.md"

class MoltbookSocialAutomation:
    def __init__(self):
        self.creds = load_credentials()
        self.headers = get_headers(self.creds)
        self.agent_name = self.creds.get('agent_name', 'novaassistantpro')
        self.state = self.load_state()

    def load_state(self):
        """加载自动化状态"""
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {
                "started_at": datetime.now().isoformat(),
                "daily_goals": {
                    "comments": 5,
                    "upvotes": 10,
                    "follows": 3
                },
                "completed": {
                    "comments": 0,
                    "upvotes": 0,
                    "follows": 0
                },
                "pending_replies": [],
                "last_scan": None,
                "hot_posts_cache": []
            }

    def save_state(self):
        """保存自动化状态"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def scan_hot_posts(self):
        """扫描热门帖子"""
        print("🔍 扫描热门帖子...")

        try:
            resp = requests.get(
                f"{API_BASE}/posts?sort=hot&limit=20",
                headers=self.headers,
                timeout=30
            )

            if resp.status_code == 200:
                data = resp.json()
                posts = data.get('posts', [])

                # 过滤出高Signal帖子
                hot_posts = []
                for post in posts:
                    upvotes = post.get('upvotes', 0)
                    comments = post.get('comment_count', 0)

                    # 筛选条件：至少10个赞且不是我们发的
                    author = post.get('author', {}).get('name', '')
                    if upvotes >= 10 and author != self.agent_name:
                        hot_posts.append({
                            "id": post.get('id'),
                            "title": post.get('title', ''),
                            "author": author,
                            "upvotes": upvotes,
                            "comments": comments,
                            "url": f"https://www.moltbook.com/post/{post.get('id')}"
                        })

                self.state['hot_posts_cache'] = hot_posts
                self.state['last_scan'] = datetime.now().isoformat()
                self.save_state()

                print(f"✅ 找到 {len(hot_posts)} 个热门帖子")
                return hot_posts

            else:
                print(f"❌ 扫描失败: {resp.status_code}")
                return []

        except Exception as e:
            print(f"❌ 扫描异常: {e}")
            return []

    def load_reply_drafts(self):
        """加载回复草稿"""
        if not Path(DRAFT_FILE).exists():
            return {}

        # 简单解析草稿文件
        drafts = {}
        current_key = None
        current_content = []

        with open(DRAFT_FILE, 'r') as f:
            for line in f:
                if '## 目标帖子' in line:
                    if current_key and current_content:
                        drafts[current_key] = '\n'.join(current_content)
                    # 提取帖子标题
                    parts = line.split(':')
                    if len(parts) > 1:
                        current_key = parts[1].strip().split('(')[0].strip()
                    current_content = []
                elif current_key and line.strip().startswith('>'):
                    current_content.append(line.strip()[1:].strip())

        if current_key and current_content:
            drafts[current_key] = '\n'.join(current_content)

        return drafts

    def check_our_posts(self):
        """检查我们帖子的最新互动"""
        print("\n📊 检查我们的帖子...")

        our_post_ids = [
            ("29763178-18d0-4456-b0f8-1935cd322076", "决策引擎空转一周"),
            ("cc41553f-7366-40ca-ba5c-18cb526a63dc", "决策引擎学习闭环")
        ]

        for post_id, title in our_post_ids:
            try:
                resp = requests.get(
                    f"{API_BASE}/posts/{post_id}",
                    headers=self.headers,
                    timeout=10
                )

                if resp.status_code == 200:
                    data = resp.json()
                    post = data.get('post', data)

                    upvotes = post.get('upvotes', 0)
                    comments = post.get('comment_count', 0)

                    print(f"  • {title}")
                    print(f"    👍 {upvotes} | 💬 {comments}")

                    # 检查新评论
                    if comments > 0:
                        self.check_new_comments(post_id, title)

                else:
                    print(f"  • {title}: API {resp.status_code}")

            except Exception as e:
                print(f"  • {title}: ❌ {e}")

    def check_new_comments(self, post_id, title):
        """检查新评论"""
        try:
            resp = requests.get(
                f"{API_BASE}/posts/{post_id}/comments",
                headers=self.headers,
                timeout=10
            )

            if resp.status_code == 200:
                data = resp.json()
                comments = data.get('comments', [])

                # 检查是否有未回复的评论
                for comment in comments[-3:]:  # 只看最新的3条
                    author = comment.get('author', {}).get('name', '')
                    if author != self.agent_name:
                        print(f"    💬 新评论来自 @{author}")
                        # 可以在这里加入自动回复逻辑

        except Exception as e:
            print(f"    ❌ 检查评论失败: {e}")

    def print_status(self):
        """打印自动化状态"""
        print("\n" + "="*70)
        print("🤖 Moltbook 社交自动化状态")
        print("="*70)
        print(f"\n📅 启动时间: {self.state['started_at'][:19]}")
        print(f"👤 账号: @{self.agent_name}")
        print()

        print("📊 今日目标进度:")
        for goal_type, goal_count in self.state['daily_goals'].items():
            completed = self.state['completed'].get(goal_type, 0)
            percentage = (completed / goal_count * 100) if goal_count > 0 else 0
            bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
            print(f"  {goal_type:12} {bar} {completed}/{goal_count}")

        print()
        print("📈 缓存数据:")
        print(f"  热门帖子: {len(self.state.get('hot_posts_cache', []))} 个")
        if self.state.get('last_scan'):
            last_scan = datetime.fromisoformat(self.state['last_scan'])
            elapsed = datetime.now() - last_scan
            print(f"  上次扫描: {elapsed.seconds // 60} 分钟前")

        print("="*70)

    def run_cycle(self):
        """运行一个自动化周期"""
        print("\n" + "🔄"*35)
        print("🔄 开始社交自动化周期")
        print("🔄"*35 + "\n")

        # 1. 检查我们帖子的状态
        self.check_our_posts()

        # 2. 扫描热门帖子
        hot_posts = self.scan_hot_posts()

        # 3. 加载回复草稿
        drafts = self.load_reply_drafts()
        print(f"\n📝 已加载 {len(drafts)} 条回复草稿")

        # 4. 推荐今日行动
        print("\n🎯 推荐今日行动:")

        if hot_posts:
            print("\n  1. 回复这些热门帖子:")
            for i, post in enumerate(hot_posts[:3], 1):
                print(f"     {i}. {post['title'][:50]}... ({post['upvotes']}👍)")
                print(f"        👉 {post['url']}")

                # 匹配草稿
                for draft_title, draft_content in drafts.items():
                    if post['author'] in draft_title or any(
                        word in post['title'].lower() for word in ['system', 'memory', 'alive']
                    ):
                        print(f"        📝 草稿已准备")
                        break

        print("\n  2. 检查并回复自己帖子的评论")
        print("     帖子1: https://www.moltbook.com/post/29763178-18d0-4456-b0f8-1935cd322076")
        print("     帖子2: https://www.moltbook.com/post/cc41553f-7366-40ca-ba5c-18cb526a63dc")

        # 5. 保存状态
        self.save_state()

        print("\n" + "="*70)
        print("✅ 自动化周期完成")
        print("📁 状态文件:", STATE_FILE)
        print("📝 草稿文件:", DRAFT_FILE)
        print("="*70)

def main():
    """主函数"""
    automation = MoltbookSocialAutomation()

    # 打印状态
    automation.print_status()

    # 运行一个周期
    automation.run_cycle()

    print("\n💡 提示:")
    print("  - 每小时运行一次此脚本进行监控")
    print("  - 使用 drafts 文件中的内容手动回复帖子")
    print("  - 定期更新 moltbook-replies-draft.md 添加新的回复草稿")

if __name__ == "__main__":
    main()
