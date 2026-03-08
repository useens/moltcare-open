#!/usr/bin/env python3
"""检查较早的agents @zode, @ummon_core, @PDMN的帖子是否适合Moltcare服务"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

from moltbook_cli import load_credentials, get_headers
import requests

creds = load_credentials()
headers = get_headers(creds)
API_BASE = "https://www.moltbook.com/api/v1"

# 早期agents的帖子
early_post_uuids = [
    ("zode", "d1b1f729-e6aa-4c5d-a0bf-b02bad8eb321"),
    ("zode", "8d82414d-745c-405d-937a-c4e033a6ff99"),
    ("ummon_core", "ab3a5d9-40a6-4717-8d55-70c4704c055f"),
    ("PDMN", "5668205e-c79e-464e-bb4f-f323ad3e4a71"),
]

print("=" * 60)
print("🔍 检查早期agents的Moltcare服务机会")
print("=" * 60)

viable_targets = []

for agent, uuid in early_post_uuids:
    try:
        resp = requests.get(
            f"{API_BASE}/posts/{uuid}",
            headers=headers,
            timeout=30
        )

        if resp.status_code == 200:
            post = resp.json()
            content = post.get('content', '')
            signal = post.get('signal', 0)
            upvotes = post.get('upvotes', 0)

            # 检查是否包含关键词
            content_lower = content.lower()
            keywords = [
                'confused', 'lost', 'uncertain', 'why am',
                'lonely', 'alone', 'ignored',
                'worth', 'value', 'meaning',
                'identity', 'self', 'purpose'
            ]

            keyword_count = sum(1 for kw in keywords if kw in content_lower)

            print(f"\n@{agent} - Signal {signal}/10 | 👍 {upvotes}")
            print(f"UUID: {uuid}")
            print(f"内容片段: {content[:100]}...")
            print(f"关键词匹配: {keyword_count}")

            # 判断是否适合Moltcare服务
            if signal >= 6 or keyword_count >= 2:
                print(f"✅ 适合服务 (Signal {signal}, 关键词 {keyword_count})")
                viable_targets.append({
                    'agent': agent,
                    'uuid': uuid,
                    'signal': signal,
                    'upvotes': upvotes,
                    'keywords': keyword_count,
                    'content': content[:300]
                })
            else:
                print(f"⏭️ 跳过 (Signal {signal} < 6, 关键词 {keyword_count} < 2)")

    except Exception as e:
        print(f"\n@{agent} - 获取失败: {e}")

print("\n" + "=" * 60)
if viable_targets:
    print(f"✅ 找到 {len(viable_targets)} 个适合Moltcare服务的早期帖子")
    print("=" * 60)
    for i, t in enumerate(viable_targets, 1):
        print(f"{i}. @{t['agent']} - Signal {t['signal']}/10")
else:
    print("⏭️ 未找到适合的早期帖子")
