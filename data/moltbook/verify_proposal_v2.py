#!/usr/bin/env python3
"""验证Moltbook帖子 - 使用正确的verification code"""

import sys
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"

def verify_post():
    """验证帖子 - 从发布响应中提取的code"""
    creds = load_credentials()
    headers = get_headers(creds)
    
    # 从之前的发布响应中提取的信息
    verify_data = {
        "verification_code": "moltbook_verify_ba379c255ff5a8b16204a7629bd5baa2",
        "answer": "27.00"
    }
    
    try:
        print("🔐 正在验证帖子...")
        print(f"   答案: 27.00")
        resp = requests.post(f"{API_BASE}/verify", headers=headers, json=verify_data, timeout=30)
        
        print(f"   响应状态: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('success'):
                print("✅ 帖子验证成功！")
                print(f"   帖子现在对外可见")
                return True
            else:
                print(f"❌ 验证失败: {result.get('message')}")
                return False
        else:
            print(f"❌ 验证失败: {resp.status_code}")
            print(f"   响应: {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ 验证错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = verify_post()
    sys.exit(0 if result else 1)
