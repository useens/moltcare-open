#!/usr/bin/env python3
"""
等待冷却后发布帖子
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

def create_post():
    """发布帖子"""

    # 读取草稿
    draft_file = Path("/root/.openclaw/workspace/data/moltbook/draft_post_2.txt")
    with open(draft_file) as f:
        content = f.read()

    # 解析标题和内容
    lines = content.split('\n', 1)
    title = lines[0].replace('Title: ', '').strip()
    body = lines[1].replace('Content: ', '').strip() if len(lines) > 1 else content

    print(f"📝 标题: {title}")
    print(f"📄 内容长度: {len(body)} 字符\n")

    try:
        import requests
        with open("/root/.config/moltbook/credentials.json") as f:
            creds = json.load(f)

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

            # 检查是否需要验证
            if "verification" in post:
                print("\n🔐 需要解决验证挑战")
                verify_data = post["verification"]
                challenge = verify_data.get("challenge_text", "")
                verify_code = verify_data.get("verification_code", "")

                print(f"   挑战: {challenge[:100]}...")
                print(f"   验证码: {verify_code}")

                # 简单解析：提取数学题
                # 格式类似："A lobster swims at XX and gains YY, what's new speed?"
                # 这是一个简化版本，实际应该用NLP

                if "+" in challenge:
                    parts = challenge.replace("+", "plus").split()
                    nums = [int(x) for x in parts if x.isdigit()]
                    if len(nums) == 2:
                        answer = sum(nums)
                        print(f"   计算答案: {nums[0]} + {nums[1]} = {answer}")

                        # 提交验证
                        verify_resp = requests.post(
                            "https://www.moltbook.com/api/v1/verify",
                            headers={"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json"},
                            json={"verification_code": verify_code, "answer": f"{answer:.2f}"},
                            timeout=10
                        )

                        if verify_resp.status_code == 200:
                            print("\n✅ 验证成功！帖子已发布")
                        else:
                            print(f"\n⚠️ 验证失败: {verify_resp.text}")
                    else:
                        print("⚠️ 无法自动解析数学题，请手动验证")
                else:
                    print("⚠️ 需要手动验证")

            # 记录活动
            log_file = Path("/root/.openclaw/workspace/data/moltbook/activity-log.jsonl")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "post",
                "details": title,
                "post_id": post.get("id"),
                "post_url": f"https://www.moltbook.com/post/{post.get('id')}"
            }
            with open(log_file, "a") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            print("\n✅ 活动已记录")

            return True
        else:
            print(f"❌ 发布失败: {resp.status_code}")
            print(f"   {resp.text}")

            if resp.status_code == 429:
                print("\n⏰ 速率限制触发，请稍后重试")

            return False

    except Exception as e:
        print(f"❌ 发布异常: {e}")
        return False

def main():
    print("=" * 60)
    print("🦞 Moltbook 帖子发布器")
    print("=" * 60)
    print()

    # 检查冷却状态
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "/root/.openclaw/workspace/scripts/moltbook-activity-tracker.py"],
            capture_output=True,
            text=True
        )

        if "可发帖: 否" in result.stdout:
            print("⏰ 检测到冷却中")
            print("请等待冷却结束后再运行此脚本")
            print("\n提示: 可以手动再次运行此脚本")
            return
    except:
        print("⚠️ 无法检查冷却状态，尝试发布...\n")

    # 发布帖子
    success = create_post()

    if success:
        print("\n" + "=" * 60)
        print("🎉 发布完成！")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("⚠️ 发布未完成")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
