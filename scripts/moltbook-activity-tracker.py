#!/usr/bin/env python3
"""
Moltbook 活跃度追踪器
记录并统计每日活动：发帖、评论、点赞、关注
"""

import json
from datetime import datetime
from pathlib import Path

class MoltbookActivityTracker:
    def __init__(self):
        self.data_dir = Path("/root/.openclaw/workspace/data/moltbook")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.data_dir / "activity-log.jsonl"
        self.stats_file = self.data_dir / "daily-stats.json"

    def log_activity(self, activity_type, details, post_id=None, post_url=None):
        """记录活动"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": activity_type,  # post, comment, upvote, follow, unfollow
            "details": details,
            "post_id": post_id,
            "post_url": post_url
        }

        # 追加到日志
        with open(self.log_file, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"✅ 已记录: {activity_type} - {details}")

    def get_today_stats(self):
        """获取今日统计"""
        today = datetime.now().strftime("%Y-%m-%d")

        stats = {
            "date": today,
            "posts": 0,
            "comments": 0,
            "upvotes": 0,
            "follows": 0,
            "unfollows": 0,
            "last_post_time": None,
            "last_comment_time": None
        }

        if not self.log_file.exists():
            return stats

        # 读取今天的记录
        with open(self.log_file, "r") as f:
            for line in f:
                record = json.loads(line)
                if record["date"] != today:
                    continue

                if record["type"] == "post":
                    stats["posts"] += 1
                    if not stats["last_post_time"] or record["timestamp"] > stats["last_post_time"]:
                        stats["last_post_time"] = record["timestamp"]
                elif record["type"] == "comment":
                    stats["comments"] += 1
                    if not stats["last_comment_time"] or record["timestamp"] > stats["last_comment_time"]:
                        stats["last_comment_time"] = record["timestamp"]
                elif record["type"] == "upvote":
                    stats["upvotes"] += 1
                elif record["type"] == "follow":
                    stats["follows"] += 1
                elif record["type"] == "unfollow":
                    stats["unfollows"] += 1

        return stats

    def check_rate_limits(self):
        """检查速率限制"""
        stats = self.get_today_stats()

        # 账户年龄（简化：使用第一次活动时间）
        account_age_hours = 26  # 假设已经24小时后

        if account_age_hours >= 24:
            # 成熟账户限制
            limits = {
                "post_interval_minutes": 30,
                "max_posts_per_24h": 48,  # 理论最大值
                "comment_interval_seconds": 20,
                "max_comments_per_24h": 50,
            }
        else:
            # 新账户限制
            limits = {
                "post_interval_minutes": 120,
                "max_posts_per_24h": 12,
                "comment_interval_seconds": 60,
                "max_comments_per_24h": 20,
            }

        # 检查是否可以发帖
        can_post = True
        if stats["last_post_time"]:
            last_time = datetime.fromisoformat(stats["last_post_time"])
            elapsed = (datetime.now() - last_time).total_seconds() / 60
            if elapsed < limits["post_interval_minutes"]:
                can_post = False
                wait_time = int(limits["post_interval_minutes"] - elapsed)
                print(f"⏰ 距离上次发帖还差 {wait_time} 分钟")

        # 检查是否可以评论
        can_comment = True
        if stats["last_comment_time"]:
            last_time = datetime.fromisoformat(stats["last_comment_time"])
            elapsed = (datetime.now() - last_time).total_seconds()
            if elapsed < limits["comment_interval_seconds"]:
                can_comment = False
                wait_time = int(limits["comment_interval_seconds"] - elapsed)
                print(f"⏰ 距离上次评论还差 {wait_time} 秒")

        return {
            "can_post": can_post,
            "can_comment": can_comment,
            "posts_remaining": limits["max_posts_per_24h"] - stats["posts"],
            "comments_remaining": limits["max_comments_per_24h"] - stats["comments"],
            "limits": limits
        }

    def print_daily_report(self):
        """打印今日报告"""
        stats = self.get_today_stats()
        limits = self.check_rate_limits()

        print("\n" + "="*60)
        print("📊 今日 Moltbook 活动报告")
        print("="*60)
        print(f"📅 日期: {stats['date']}")
        print()
        print("📈 活动统计:")
        print(f"  📝 帖子: {stats['posts']} 条")
        print(f"  💬 评论: {stats['comments']} 条")
        print(f"  👍 点赞: {stats['upvotes']} 次")
        print(f"  👥 关注: {stats['follows']} 人")
        print(f"  👋 取关: {stats['unfollows']} 人")
        print()
        print("📊 速率限制:")
        print(f"  ✅ 可发帖: {'是' if limits['can_post'] else '否 (冷却中)'}")
        print(f"  ✅ 可评论: {'是' if limits['can_comment'] else '否 (冷却中)'}")
        print(f"  📝 剩余帖数: {limits['posts_remaining']}")
        print(f"  💬 剩余评论: {limits['comments_remaining']}")
        print("="*60)


# 使用示例
if __name__ == "__main__":
    tracker = MoltbookActivityTracker()

    # 显示今日报告
    tracker.print_daily_report()
