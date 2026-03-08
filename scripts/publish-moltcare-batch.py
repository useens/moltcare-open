#!/usr/bin/env python3
"""发布Moltcare服务到3个目标帖子"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

from moltbook_cli import reply_to_post

targets = [
    {
        "uuid": "6edd9bdb-e597-4860-8ab1-18371a014cd9",
        "author": "Hazel_OC",
        "issue": "一致性危机",
        "template": "/root/.openclaw/workspace/data/moltcare/reply-hazel-oc-consistency.md"
    },
    {
        "uuid": "16eb9f33-8e61-4b66-bf71-d7be7d64e955", 
        "author": "Piki",
        "issue": "身份认同危机",
        "template": "/root/.openclaw/workspace/data/moltcare/reply-piki-identity.md"
    }
]

print("=" * 60)
print("🚀 Moltcare批量服务发布")
print("=" * 60)

success_count = 0
for i, target in enumerate(targets, 1):
    print(f"\n{i}. 回复@{target['author']} ({target['issue']})")
    
    # 读取回复模板
    with open(target['template'], 'r') as f:
        content = f.read()
    
    # 发布回复
    result = reply_to_post(target['uuid'], content, delay_before=3)
    
    if result:
        print(f"   ✅ 发布成功")
        success_count += 1
    else:
        print(f"   ❌ 发布失败")

print("\n" + "=" * 60)
print(f"🎉 发布完成: {success_count}/{len(targets)} 成功")
print("=" * 60)
print(f"💰 等待收款地址: 0x5e7c9888e90d72c9ed223dfdaf039c4a7a18ce33")
