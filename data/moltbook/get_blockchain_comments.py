#!/usr/bin/env python3
"""查看Blockchain Memory Proposal的评论"""

import sys
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"
POST_ID = "14ee16be-fffb-4e36-93c7-33fc6724a455"

def get_comments():
    creds = load_credentials()
    headers = get_headers(creds)
    
    try:
        resp = requests.get(f"{API_BASE}/posts/{POST_ID}/comments", headers=headers, timeout=30)
        if resp.status_code == 200:
            comments = resp.json().get('comments', [])
            print(f"📊 找到 {len(comments)} 条评论\n")
            
            for i, c in enumerate(comments, 1):
                author = c.get('author', {}).get('name', 'Unknown')
                content = c.get('content', '')
                cid = c.get('id')
                
                print(f"[{i}] @{author}")
                print(f"    ID: {cid}")
                print(f"    内容: {content[:300]}...")
                print()
            
            return comments
    except Exception as e:
        print(f"❌ 错误: {e}")
    return []

if __name__ == "__main__":
    print("="*70)
    print("💬 Blockchain Memory Proposal - 评论列表")
    print("="*70)
    get_comments()
