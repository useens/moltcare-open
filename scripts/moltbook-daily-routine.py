#!/usr/bin/env python3
"""
Moltbook 每日互动脚本
自动执行：浏览、点赞、评论（可选）、检查消息
"""

import random
import time
import subprocess
import sys
from datetime import datetime

# 默认值
TARGET_REPLIES = 5
TARGET_UPVOTES = 10
TARGET_COMMENTS = 3

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60)

def check_rate_limits():
    """检查速率限制"""
    try:
        result = subprocess.run(
            [sys.executable, "/root/.openclaw/workspace/scripts/moltbook-activity-tracker.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(result.stdout)
            return True
    except Exception as e:
        print(f"⚠️ 无法检查速率限制: {e}")
    return False

def browse_and_upvote():
    """浏览并点赞优质帖子"""
    print_header("🔍 浏览帖子并点赞")

    # 使用 curl 获取热门帖子
    print("📥 获取热门帖子...")
    try:
        import json
        import requests

        creds = {}
        try:
            with open("/root/.config/moltbook/credentials.json") as f:
                creds = json.load(f)
        except:
            print("❌ 无法读取凭证")
            return 0

        resp = requests.get(
            "https://www.moltbook.com/api/v1/posts?sort=new&limit=15",
            headers={"Authorization": f"Bearer {creds['api_key']}"},
            timeout=15
        )

        if resp.status_code != 200:
            print(f"❌ 获取帖子失败: {resp.status_code}")
            return 0

        data = resp.json()
        posts = data.get("posts", [])

        print(f"✅ 获取到 {len(posts)} 条帖子\n")

        upvoted = 0
        for i, post in enumerate(posts[:TARGET_UPVOTES], 1):
            title = post.get("title", "")[:50]
            author = post.get("author", {}).get("name", "unknown")
            score = post.get("upvotes", 0)
            comments = post.get("comment_count", 0)

            print(f"[{i}] {title}...")
            print(f"    作者: {author} | 👍{score} | 💬{comments}")

            # 随机点赞策略：高质量帖子（点赞多或评论多）更容易获赞
            # 新帖子也倾向于点赞
            if score > 5 or comments > 3 or random.random() > 0.5:
                print(f"    👍 点赞")
                # 实际点赞
                try:
                    upvote_resp = requests.post(
                        f"https://www.moltbook.com/api/v1/posts/{post['id']}/upvote",
                        headers={"Authorization": f"Bearer {creds['api_key']}"},
                        timeout=10
                    )
                    if upvote_resp.status_code == 200:
                        upvoted += 1
                        print(f"    ✅ 点赞成功")
                        # 记录活动
                        record_activity('upvote', f"{title} (by {author})", post['id'])
                    else:
                        print(f"    ⚠️ 点赞失败: {upvote_resp.status_code}")
                except Exception as e:
                    print(f"    ⚠️ 点赞异常: {e}")

            print()

        return upvoted

    except Exception as e:
        print(f"❌ 浏览异常: {e}")
        return 0

def record_activity(activity_type, details, post_id=None):
    """记录活动到日志"""
    import json
    from pathlib import Path

    log_file = Path("/root/.openclaw/workspace/data/moltbook/activity-log.jsonl")
    record = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": activity_type,
        "details": details,
        "post_id": post_id
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def print_summary(upvotes):
    """打印汇总"""
    print_header("📊 今日活动汇总")
    print(f"👍 点赞: {upvotes} 次")
    print(f"💬 评论: 0 次 (手动添加)")
    print(f"📝 发帖: 0 条 (手动添加)")
    print("\n💡 提示:")
    print("  • 定期运行此脚本保持活跃")
    print("  • 手动进行评论和发帖以保持真实互动")
    print("  • 点赞无严格限制，适度即可")
    print("="*60)

def main():
    """主函数"""
    print_header("🦞 Moltbook 每日互动")

    # 检查速率限制
    check_rate_limits()
    time.sleep(1)

    # 浏览并点赞
    upvoted = browse_and_upvote()
    time.sleep(1)

    # 打印汇总
    print_summary(upvoted)

if __name__ == "__main__":
    main()
