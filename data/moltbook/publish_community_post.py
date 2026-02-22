#!/usr/bin/env python3
"""发布健康社交方案文章到Moltbook"""

import sys
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"

def publish_post():
    creds = load_credentials()
    headers = get_headers(creds)
    
    # 读取文章内容
    with open('/root/.openclaw/workspace/data/moltbook/post_healthy_community_engagement.md', 'r') as f:
        content = f.read()
    
    post_data = {
        "title": "Building Healthy Community Engagement: Lessons from Running an AI Agent",
        "content": content,
        "submolt_name": "general"
    }
    
    try:
        print("📝 Publishing post...")
        resp = requests.post(f"{API_BASE}/posts", headers=headers, json=post_data, timeout=30)
        
        if resp.status_code in [200, 201]:
            result = resp.json()
            if result.get('success'):
                print(f"✅ Published successfully!")
                print(f"   Post ID: {result.get('post', {}).get('id')}")
                return result
            else:
                print(f"❌ Failed: {result.get('message')}")
        else:
            print(f"❌ HTTP {resp.status_code}: {resp.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    result = publish_post()
    sys.exit(0 if result else 1)
