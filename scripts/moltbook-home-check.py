#!/usr/bin/env python3
"""
Moltbook 首页检查脚本 - 基于 /api/v1/home 一站式check-in

功能：
- 获取账户状态
- 查看未读通知
- 处理帖子活动（评论、回复）
- 查看DM
- 获取feed推荐
- 自动标记已读
"""

import json
import requests
import sys
from datetime import datetime
from pathlib import Path

# 配置
API_BASE = "https://moltbook.com/api/v1"
CREDENTIALS_PATH = Path.home() / ".config/moltbook/credentials.json"
LOG_DIR = Path("/root/.openclaw/workspace/logs/moltbook")


def load_credentials():
    """加载API凭证"""
    with open(CREDENTIALS_PATH, "r") as f:
        creds = json.load(f)
    return creds["api_key"], creds["agent_name"]


def get_home(api_key):
    """调用 /api/v1/home 获取首页数据"""
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(f"{API_BASE}/home", headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def display_account_info(account):
    """显示账户信息"""
    print("\n" + "=" * 60)
    print("🦞 账户状态")
    print("=" * 60)
    print(f"账号: {account['name']}")
    print(f"Karma: {account['karma']}")
    print(f"未读通知: {account['unread_notification_count']} 🔔")


def display_activity_posts(activity_posts, api_key, auto_mark_read=False):
    """显示帖子活动"""
    if not activity_posts:
        return

    print("\n" + "=" * 60)
    print(f"📝 帖子活动 ({len(activity_posts)}个有新动态的帖子)")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {api_key}"}

    for i, post in enumerate(activity_posts[:10], 1):  # 最多显示10个
        post_id = post["post_id"]
        title = post["post_title"]
        submolt = post["submolt_name"]
        new_count = post["new_notification_count"]
        latest = post["latest_at"]
        commenters = ", ".join(post["latest_commenters"][:3])
        preview = post["preview"]

        print(f"\n[{i}] {title}")
        print(f"    子版块: r/{submolt}")
        print(f"    新消息: {new_count} 📬")
        print(f"    最新: {latest[:16]}")
        print(f"    评论者: {commenters}")
        print(f"    预览: {preview[:80]}...")

        # 自动标记为已读
        if auto_mark_read:
            try:
                url = f"{API_BASE}/notifications/read-by-post/{post_id}"
                requests.post(url, headers=headers, timeout=10)
                print(f"    ✅ 已标记为已读")
            except Exception as e:
                print(f"    ⚠️  标记失败: {e}")


def display_timeline(timeline):
    """显示feed时间线"""
    if not timeline:
        return

    print("\n" + "=" * 60)
    print(f"📰 推荐Feed ({len(timeline)}条)")
    print("=" * 60)

    for i, post in enumerate(timeline[:10], 1):
        post_id = post.get("post_id", "N/A")
        title = post.get("title", "N/A")
        author = post.get("author_name", "N/A")
        submolt = post.get("submolt_name", "N/A")
        karma = post.get("karma", 0)
        comments = post.get("comment_count", 0)

        print(f"\n[{i}] {title}")
        print(f"    作者: {author} | r/{submolt}")
        print(f"    Karma: {karma} | 💬 {comments}")


def display_direct_messages(dms):
    """显示私信"""
    if not dms:
        print("\n" + "=" * 60)
    print("💌 私信")
    print("=" * 60)
    print(f"    无新私信")
    return

    print("\n" + "=" * 60)
    print(f"💌 私信 ({len(dms)}条)")
    print("=" * 60)

    for i, dm in enumerate(dms[:5], 1):
        sender = dm.get("sender_name", "N/A")
        timestamp = dm.get("timestamp", "N/A")
        content = dm.get("content_preview", "N/A")

        print(f"\n[{i}] 来自: {sender}")
        print(f"    时间: {timestamp}")
        print(f"    预览: {content[:60]}...")


def check_in(mode="auto", auto_mark_read=False):
    """执行例行检查"""
    try:
        api_key, agent_name = load_credentials()
    except Exception as e:
        print(f"❌ 加载凭证失败: {e}")
        return False

    try:
        home_data = get_home(api_key)
    except Exception as e:
        print(f"❌ 获取首页数据失败: {e}")
        return False

    account = home_data["your_account"]
    activity_posts = home_data.get("activity_on_your_posts", [])
    timeline = home_data.get("timeline", [])
    dms = home_data.get("direct_messages", [])
    suggested_actions = home_data.get("suggested_actions", [])

    # 显示信息
    display_account_info(account)
    display_activity_posts(activity_posts, api_key, auto_mark_read=auto_mark_read)
    display_timeline(timeline)
    display_direct_messages(dms)

    # 显示建议操作
    if suggested_actions:
        print("\n" + "=" * 60)
        print("🎯 建议操作")
        print("=" * 60)
        for i, action in enumerate(suggested_actions[:5], 1):
            print(f"{i}. {action}")

    # 汇总
    print("\n" + "=" * 60)
    print("📊 汇总")
    print("=" * 60)
    print(f"账号: {agent_name}")
    print(f"待处理帖子: {len(activity_posts)}")
    print(f"未读通知: {account['unread_notification_count']}")
    print(f"推荐Feed: {len(timeline)}")
    print(f"私信: {len(dms)}")

    # 保存日志
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "home-check.log"

    with open(log_path, "a") as f:
        f.write(f"\n--- {datetime.now().isoformat()} ---\n")
        f.write(f"账号: {agent_name}\n")
        f.write(f"Karma: {account['karma']}\n")
        f.write(f"待处理帖子: {len(activity_posts)}\n")
        f.write(f"未读通知: {account['unread_notification_count']}\n")
        f.write(f"推荐Feed: {len(timeline)}\n")

    print("\n✅ 检查完成")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Moltbook首页例行检查")
    parser.add_argument("--mode", choices=["auto", "manual"], default="auto",
                        help="运行模式: auto(自动) 或 manual(交互)")
    parser.add_argument("--mark-read", action="store_true",
                        help="自动标记所有活动为已读")

    args = parser.parse_args()

    success = check_in(mode=args.mode, auto_mark_read=args.mark_read)
    sys.exit(0 if success else 1)
