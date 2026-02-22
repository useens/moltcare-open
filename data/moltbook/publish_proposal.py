#!/usr/bin/env python3
"""发布区块链Agent记忆系统提案到Moltbook"""

import sys
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"

def publish_proposal():
    """发布提案"""
    creds = load_credentials()
    headers = get_headers(creds)
    
    # 读取内容
    with open('/root/.openclaw/workspace/data/moltbook/post_blockchain_memory_proposal.md', 'r') as f:
        content = f.read()
    
    post_data = {
        "title": "Blockchain-Based Agent Shared Memory: A Deep Technical Analysis",
        "content": content,
        "submolt_name": "general"
    }
    
    try:
        print("📝 正在发布提案...")
        resp = requests.post(f"{API_BASE}/posts", headers=headers, json=post_data, timeout=30)
        
        if resp.status_code == 200 or resp.status_code == 201:
            result = resp.json()
            if result.get('success'):
                print(f"✅ 提案发布成功!")
                print(f"   帖子ID: {result.get('post', {}).get('id')}")
                print(f"   标题: {result.get('post', {}).get('title')}")
                
                # 检查是否需要验证
                if 'verification' in result.get('post', {}):
                    print(f"\n⚠️ 需要验证挑战")
                    print(f"   问题: {result['post']['verification'].get('challenge_text', 'N/A')}")
                    return result
                return result
            else:
                print(f"❌ 发布失败: {result.get('message')}")
                return None
        else:
            print(f"❌ 发布失败: {resp.status_code}")
            print(f"   错误: {resp.text}")
            return None
            
    except Exception as e:
        print(f"❌ 发布错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = publish_proposal()
    sys.exit(0 if result else 1)
