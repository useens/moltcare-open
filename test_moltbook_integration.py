#!/usr/bin/env python3
"""测试 Moltbook API 集成"""
import sys
import json
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/scripts')

# Import engine parts
import requests

def test_moltbook_api():
    """测试 Moltbook API 是否工作"""
    creds_file = Path("/root/.config/moltbook/credentials.json")
    if not creds_file.exists():
        print("❌ Moltbook 凭证文件不存在")
        return False

    with open(creds_file) as f:
        creds = json.load(f)

    headers = {
        "Authorization": f"Bearer {creds['api_key']}",
        "Content-Type": "application/json"
    }

    # 测试搜索
    print("🔍 测试 Moltbook API 搜索...")
    resp = requests.get(
        "https://www.moltbook.com/api/v1/posts?sort=top&limit=10",
        headers=headers,
        timeout=15
    )

    if resp.status_code == 200:
        posts = resp.json().get("posts", [])
        print(f"✅ API 工作正常，获取到 {len(posts)} 个帖子")

        # 查找特定的 memory 相关帖子
        for post in posts[:5]:
            title = post.get("title", "")
            print(f"   - {title[:60]}...")

        return True
    else:
        print(f"❌ API 错误: {resp.status_code}")
        return False

if __name__ == "__main__":
    test_moltbook_api()
