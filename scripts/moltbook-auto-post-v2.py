#!/usr/bin/env python3
"""
修正后的自动发布脚本
考虑到新账户的72分钟限制
"""

import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

def check_post_status():
    """检查当前发帖状态"""
    creds = {}
    try:
        with open("/root/.config/moltbook/credentials.json") as f:
            creds = json.load(f)
    except:
        print("❌ 无法读取凭证")
        return False, None

    # 检查活动日志，获取最后发帖时间
    log_file = Path("/root/.openclaw/workspace/data/moltbook/activity-log.jsonl")

    if not log_file.exists():
        print("没有发帖记录，可以发帖")
        return True, creds

    last_post_time = None
    with open(log_file, "r") as f:
        for line in f:
            record = json.loads(line)
            if record.get("type") == "post":
                last_post_time = datetime.fromisoformat(record["timestamp"])

    if not last_post_time:
        return True, creds

    # 新账户：需要等待72分钟
    wait_time = timedelta(minutes=72)
    elapsed = datetime.now() - last_post_time

    if elapsed < wait_time:
        remaining = wait_time - elapsed
        print(f"⏰ 距离上次发帖仅过 {elapsed.total_seconds()/60:.0f} 分钟")
        print(f"⏳ 需要再等待 {remaining.total_seconds()/60:.0f} 分钟")
        return False, creds

    print(f"✅ 冷却时间已过，距离上次发帖 {elapsed.total_seconds()/60:.0f} 分钟")
    return True, creds

def main():
    """主函数"""
    print("="*60)
    print("🦞 Moltbook 自动发布（修正版）")
    print("="*60)
    print()

    can_post, creds = check_post_status()

    if not can_post:
        print("\n⏰ 需要等待冷却时间结束")
        print("脚本将每小时自动检查，直到可以发帖")
        return

    # 读取帖子草稿
    draft_file = Path("/root/.openclaw/workspace/data/moltbook/draft_post_2.txt")
    with open(draft_file) as f:
        content = f.read()

    lines = content.split('\n', 1)
    title = lines[0].replace('Title: ', '').strip()
    body = lines[1].replace('Content: ', '').strip() if len(lines) > 1 else content

    print(f"📝 准备发布帖子:")
    print(f"   标题: {title}")
    print(f"   长度: {len(body)} 字符\n")

    # 发布
    try:
        data = {
            "submolt_name": "general",
            "title": title,
            "content": body
        }

        print("📤 正在发布...\n")
        resp = requests.post(
            "https://www.moltbook.com/api/v1/posts",
            headers={
                "Authorization": f"Bearer {creds['api_key']}",
                "Content-Type": "application/json"
            },
            json=data,
            timeout=15
        )

        if resp.status_code == 200:
            result = resp.json()
            post = result.get("post", result)

            print("✅ 帖子创建成功！")
            print(f"   Post ID: {post.get('id')}")
            print(f"   URL: https://www.moltbook.com/post/{post.get('id')}")

            # 验证挑战
            if "verification" in post:
                print("\n🔐 需要解决验证挑战")

                # 简化处理：只是记录信息
                verify_data = post["verification"]
                challenge = verify_data.get("challenge_text", "")
                print(f"   挑战: {challenge[:80]}...")
                print("   请手动访问帖子页面完成验证")

            # 记录活动
            log_file = Path("/root/.openclaw/workspace/data/moltbook/activity-log.jsonl")
            with open(log_file, "a") as f:
                record = {
                    "timestamp": datetime.now().isoformat(),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "post",
                    "details": title,
                    "post_id": post.get("id"),
                    "post_url": f"https://www.moltbook.com/post/{post.get('id')}"
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            print("\n✅ 活动已记录")

        else:
            print(f"❌ 发布失败: {resp.status_code}")
            print(f"   {resp.text}")

            if resp.status_code == 429:
                error = resp.json()
                wait = error.get("retry_after_minutes", 60)
                print(f"\n⏰ 还需要等待 {wait} 分钟")

    except Exception as e:
        print(f"❌ 发布异常: {e}")

if __name__ == "__main__":
    main()
