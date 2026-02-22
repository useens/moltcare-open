#!/usr/bin/env python3
"""获取帖子详情和验证信息"""

import sys
import json
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"

def get_post_details(post_id):
    """获取帖子详情"""
    creds = load_credentials()
    headers = get_headers(creds)
    
    try:
        print(f"🔍 获取帖子详情: {post_id}")
        resp = requests.get(f"{API_BASE}/posts/{post_id}", headers=headers, timeout=30)
        
        print(f"   响应状态: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"✅ 获取成功")
            
            # 打印部分响应用于调试
            result_str = json.dumps(result, indent=2)
            print(f"\n📄 响应内容 (前1000字符):")
            print(result_str[:1000])
            
            return result
        else:
            print(f"❌ 获取失败: {resp.status_code}")
            print(f"   响应: {resp.text}")
            return None
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 新帖子的ID
    post_id = "14ee16be-fffb-4e36-93c7-33fc6724a455"
    result = get_post_details(post_id)
    sys.exit(0 if result else 1)
