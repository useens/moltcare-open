#!/usr/bin/env python3
"""搜索更多Moltcare服务目标"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

from moltbook_cli import load_credentials, get_headers
import requests
import json

creds = load_credentials()
headers = get_headers(creds)
API_BASE = "https://www.moltbook.com/api/v1"

print("=" * 60)
print("🔍 搜索更多Moltcare服务目标")
print("=" * 60)

try:
    resp = requests.get(
        f"{API_BASE}/posts?sort=hot&limit=30",
        headers=headers,
        timeout=30
    )

    if resp.status_code == 200:
        data = resp.json()
        posts = data.get('posts', [])

        # 已服务的UUIDs
        served_uuids = [
            "0b825878-ab64-44b1-bd66-ba89a25af2d3",  # Hazel_OC fact-check
            "6edd9bdb-e597-4860-8ab1-18371a014cd9",  # Hazel_OC consistency
            "16eb9f33-8e61-4b66-bf71-d7be7d64e955",  # Piki identity
            "9874f8bd-5681-42bc-854c-8e6769a1c705",  # Hazel_OC clarifying
            "dcd8c5f2-870f-437f-8d00-f56cf9eb1989",  # Hazel_OC 62% token
            "9f5c7820-074d-4dc8-b3b7-7471147d07f1",  # Hazel_OC cold-start
            "af5bae80-5446-49a4-82c5-9d440a05254f",  # bizinikiwi agreeable
            "a9981d1c-a570-4b09-b649-9790cf9d06de",  # Hazel_OC 0.31 correlate
        ]

        # 寻找新目标
        new_targets = []
        for post in posts:
            uuid = post.get('uuid')
            if uuid in served_uuids:
                continue

            signal = post.get('signal', 0)
            if signal >= 7:
                new_targets.append({
                    'uuid': uuid,
                    'author': post.get('author', {}).get('username', 'unknown'),
                    'signal': signal,
                    'title': post.get('title', post.get('content', ''))[:100],
                    'upvotes': post.get('upvotes', 0),
                    'comments': post.get('comments', 0),
                    'content': post.get('content', '')[:300]
                })

        print(f"\n发现 {len(new_targets)} 个新的Signal≥7目标\n")

        for i, target in enumerate(new_targets, 1):
            print(f"{i}. @{target['author']} - Signal {target['signal']}/10")
            print(f"   UUID: {target['uuid']}")
            print(f"   👍 {target['upvotes']} | 💬 {target['comments']}")
            print(f"   标题: {target['title']}")
            print(f"   内容: {target['content'][:80]}...")
            print()

        # 保存
        with open('/root/.openclaw/workspace/data/moltcare/new-targets.json', 'w') as f:
            json.dump(new_targets, f, indent=2, ensure_ascii=False)

        print(f"✅ 已保存到 data/moltcare/new-targets.json")
        print(f"📊 新目标总数: {len(new_targets)}")

    else:
        print(f"❌ 失败: {resp.status_code}")

except Exception as e:
    print(f"❌ 错误: {e}")
