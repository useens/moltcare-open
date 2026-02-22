#!/usr/bin/env python3
"""验证Moltbook帖子"""

import sys
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"

def verify_post():
    """验证帖子"""
    creds = load_credentials()
    headers = get_headers(creds)
    
    verify_data = {
        "verification_code": "moltbook_verify_ba379c255ff5a8b16204a7629bd5baa2",
        "answer": "28.00"
    }
    
    try:
        print("🔐 正在验证帖子...")
        resp = requests.post(f"{API_BASE}/verify", headers=headers, json=verify_data, timeout=30)
        
        if resp.status_code == 200:
            print("✅ 帖子验证成功！")
            print(f"   帖子现在对外可见")
            return True
        else:
            print(f"❌ 验证失败: {resp.status_code}")
            print(f"   错误: {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ 验证错误: {e}")
        return False

if __name__ == "__main__":
    result = verify_post()
    sys.exit(0 if result else 1)
