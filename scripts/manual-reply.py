#!/usr/bin/env python3
"""
手动回复助手 - 更新统一状态
用于手动回复帖子时更新状态，避免自动回复重复
"""

import json
import requests
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import moltbook_unified_state as state_manager

def load_credentials():
    creds_file = Path("/root/.config/moltbook/credentials.json")
    with open(creds_file) as f:
        return json.load(f)

def send_manual_reply(post_id, content):
    """
    手动发送回复并更新统一状态
    用法: python3 scripts/manual-reply.py <post_id> <reply_content>
    """
    API_BASE = "https://www.moltbook.com/api/v1"
    
    # 先检查是否应该回复
    can_reply, reason = state_manager.check_should_reply(post_id)
    if not can_reply:
        print(f"⚠️  {reason}")
        return False
    
    creds = load_credentials()
    headers = {
        "Authorization": f"Bearer {creds['api_key']}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(
            f"{API_BASE}/posts/{post_id}/comments",
            headers=headers,
            json={"content": content, "parent_id": None},
            timeout=10
        )
        
        if resp.status_code in [200, 201]:
            # 记录到统一状态
            state_manager.record_reply(post_id, is_manual=True)
            print("✅ 手动回复发送成功，已更新统一状态")
            return True
        else:
            print(f"❌ 回复失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 scripts/manual-reply.py <post_id> <reply_content>")
        print("示例: python3 scripts/manual-reply.py abc-123 '@author Great post!'")
        sys.exit(1)
    
    post_id = sys.argv[1]
    content = ' '.join(sys.argv[2:])
    
    send_manual_reply(post_id, content)
