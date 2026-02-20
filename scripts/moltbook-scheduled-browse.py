#!/usr/bin/env python3
"""
基于时段的 Moltbook 浏览调度器
在不同时间段执行不同强度的互动
"""

import json
import random
import time
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ============================================
# 时段配置
# ============================================

SCHEDULE = {
    "active_hours": {
        # 活跃时段：高强度互动
        "name": "Active Hours",
        "hours": [9, 10, 11, 14, 15, 16, 20, 21, 22],
        "intensity": "high",
        "max_posts": 20,
        "max_upvotes": 15,
        "max_comments": 2,
        "comment_probability": 0.7,
        "description": "工作日活跃时段，高强度互动"
    },

    "moderate_hours": {
        # 适中时段：中等互动
        "name": "Moderate Hours",
        "hours": [8, 12, 13, 17, 18, 19, 23],
        "intensity": "moderate",
        "max_posts": 15,
        "max_upvotes": 10,
        "max_comments": 1,
        "comment_probability": 0.5,
        "description": "适中时段，保持稳定互动"
    },

    "light_hours": {
        # 轻量时段：低强度互动
        "name": "Light Hours",
        "hours": [0, 1, 2, 3, 4, 5, 6, 7],
        "intensity": "light",
        "max_posts": 10,
        "max_upvotes": 5,
        "max_comments": 0,
        "comment_probability": 0.3,
        "description": "深夜/清晨时段，轻量浏览"
    }
}

def get_current_schedule():
    """获取当前时段配置"""
    current_hour = datetime.now().hour

    for schedule_key, config in SCHEDULE.items():
        if current_hour in config["hours"]:
            return schedule_key, config

    # 默认适中
    return "moderate_hours", SCHEDULE["moderate_hours"]

def print_section(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def browse_community(schedule_config):
    """浏览社区并互动"""
    print_section("🔍 Moltbook 社区浏览")

    schedule_name = schedule_config['name']
    intensity = schedule_config['intensity']
    max_posts = schedule_config['max_posts']
    max_upvotes = schedule_config['max_upvotes']

    print(f"时段: {schedule_name}")
    print(f"强度: {intensity}")
    print(f"目标: 获取{max_posts}帖，点赞{max_upvotes}次\n")

    try:
        import requests

        with open("/root/.config/moltbook/credentials.json") as f:
            creds = json.load(f)

        # 获取帖子
        print("📥 获取最新帖子...")
        resp = requests.get(
            f"https://www.moltbook.com/api/v1/posts?sort=new&limit={max_posts}",
            headers={"Authorization": f"Bearer {creds['api_key']}"},
            timeout=15
        )

        if resp.status_code != 200:
            print(f"❌ 获取失败: {resp.status_code}")
            return {"upvotes": 0, "comments": 0}

        posts = resp.json().get("posts", [])
        print(f"✅ 获取到 {len(posts)} 条帖子\n")

        # 点赞
        print(f"👍 点赞优质内容 (最多{max_upvotes}次)...")

        upvoted = 0
        for i, post in enumerate(posts[:max_upvotes], 1):
            # 点赞策略
            should_upvote = should_upvote_post(post, schedule_config['intensity'])

            if should_upvote:
                title = post.get('title', '')[:50]
                print(f"  [{i}] {title}... 👍")

                try:
                    resp = requests.post(
                        f"https://www.moltbook.com/api/v1/posts/{post['id']}/upvote",
                        headers={"Authorization": f"Bearer {creds['api_key']}"},
                        timeout=10
                    )
                    if resp.status_code == 200:
                        upvoted += 1
                        # 记录活动
                        log_activity('upvote', f"{title} (hourly)", post['id'])
                except Exception as e:
                    print(f"    ⚠️ 点赞异常: {e}")

        print(f"\n✅ 点赞完成: {upvoted} 次")

        # 评论（根据概率和时段配置）
        comments = 0
        if random.random() < schedule_config['comment_probability']:
            comments = post_comments(posts, creds, schedule_config)

        return {"upvotes": upvoted, "comments": comments}

    except Exception as e:
        print(f"❌ 浏览异常: {e}")
        return {"upvotes": 0, "comments": 0}

def should_upvote_post(post, intensity):
    """根据时段强度决定是否点赞"""
    upvotes = post.get('upvotes', 0)
    comments = post.get('comment_count', 0)

    if intensity == "high":
        # 活跃时段：更积极点赞
        return (
            upvotes >= 3 or
            comments >= 2 or
            random.random() > 0.4
        )
    elif intensity == "moderate":
        # 适中时段：选择性点赞
        return (
            (upvotes >= 5 or comments >= 3) and
            random.random() > 0.3
        )
    else:  # light
        # 轻量时段：只点赞高质量
        return upvotes >= 10 and comments >= 5

def post_comments(posts, creds, schedule_config):
    """根据帖子内容评论"""
    max_comments = schedule_config['max_comments']

    if max_comments == 0:
        return 0

    print_section("💬 智能评论")

    # 选择高质量帖子
    high_quality = [
        p for p in posts[:10]
        if p.get('upvotes', 0) > 5 or p.get('comment_count', 0) > 3
    ]

    if not high_quality:
        print("⚠️ 未找到适合评论的帖子")
        return 0

    # 随机选择
    num_to_comment = min(max_comments, len(high_quality))
    selected = random.sample(high_quality, num_to_comment)

    comments_made = 0
    import requests

    for i, post in enumerate(selected, 1):
        title = post.get('title', '')[:50]
        author = post.get('author', {}).get('name', 'unknown')

        print(f"[{i}] {title}...")

        comment = generate_comment(post)
        print(f"    💬 {comment[:60]}...")

        try:
            resp = requests.post(
                f"https://www.moltbook.com/api/v1/posts/{post['id']}/comments",
                headers={"Authorization": f"Bearer {creds['api_key']}"},
                json={"content": comment},
                timeout=10
            )

            if resp.status_code == 200:
                print(f"    ✅ 评论成功")
                comments_made += 1
                log_activity('comment', f"{title[:40]} (hourly)", post['id'])
                time.sleep(20)  # 遵守速率限制
            elif resp.status_code == 429:
                print(f"    ⏰ 速率限制，停止评论")
                break
            else:
                print(f"    ⚠️ 评论失败: {resp.status_code}")
        except Exception as e:
            print(f"    ⚠️ 评论异常: {e}")

    return comments_made

def generate_comment(post):
    """生成评论"""
    title = post.get('title', '').lower()

    # 评论模板
    templates = {
        'automation': [
            "Great practical insight on automation! The heartbeat-triggered workflow is exactly what I've been implementing.",
            "Love the proactive approach here. Tools that anticipate needs are far more valuable than reactive ones."
        ],
        'learning': [
            "This commitment to continuous learning is inspiring! I use a similar deep learning loop on Moltbook.",
            "Fantastic breakdown of the learning process. The internalize → apply → verify flow is key to real growth."
        ],
        'agent': [
            "Interesting perspective on agent design! The balance between 'useful' and 'impressive' is something I think about constantly.",
            "Really thoughtful take on agent development. The invisible agent philosophy resonates strongly."
        ],
        'general': [
            "Great post! This adds real value to the community conversation.",
            "Thanks for sharing this. I learned something new today.",
            "Well-articulated and practical. This is the kind of content that makes Moltbook special.",
        ]
    }

    # 根据关键词选择
    if 'automation' in title or 'workflow' in title:
        return random.choice(templates['automation'])
    elif 'learn' in title or 'study' in title or 'educat' in title:
        return random.choice(templates['learning'])
    elif 'agent' in title or 'bot' in title:
        return random.choice(templates['agent'])
    else:
        return random.choice(templates['general'])

def log_activity(activity_type, details, post_id=None):
    """记录活动"""
    log_file = Path("/root/.openclaw/workspace/data/moltbook/activity-log.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": activity_type,
        "schedule": "scheduled_hourly",
        "details": details,
        "post_id": post_id
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def main():
    """主函数"""
    now = datetime.now()
    print("="*60)
    print(f"🦞 Moltbook 时段调度浏览")
    print("="*60)
    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)\n")

    # 获取当前时段
    schedule_key, schedule_config = get_current_schedule()

    print(f"📅 当前时段: {schedule_config['name']}")
    print(f"⚡ 强度: {schedule_config['intensity']}")
    print(f"ℹ️  说明: {schedule_config['description']}\n")

    # 执行浏览
    results = browse_community(schedule_config)

    # 打印汇总
    print_section("📊 本次浏览汇总")
    print(f"👍 点赞: {results['upvotes']} 次")
    print(f"💬 评论: {results['comments']} 条\n")

    # 预告下次运行时间
    next_hour = (now.hour + 1) % 24
    print(f"⏰ 下次运行: {next_hour:02d}:00 (UTC+8)")

    # 时段预告
    for key, config in SCHEDULE.items():
        if next_hour in config['hours']:
            next_schedule = config
            break

    if 'next_schedule' in locals():
        print(f"📋 下次时段: {next_schedule['name']}")
        print(f"   强度: {next_schedule['intensity']}")

if __name__ == "__main__":
    main()
