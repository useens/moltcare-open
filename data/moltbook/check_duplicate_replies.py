#!/usr/bin/env python3
"""检查是否有重复回复的情况"""

import sys
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"

def check_post_replies(post_id, post_title, my_name='novaassistantpro'):
    """检查帖子下的所有评论，找出我的多次回复"""
    creds = load_credentials()
    headers = get_headers(creds)
    
    try:
        resp = requests.get(f"{API_BASE}/posts/{post_id}/comments", headers=headers, timeout=30)
        if resp.status_code != 200:
            return
        
        comments = resp.json().get('comments', [])
        
        # 建立parent_id -> 我的回复列表 的映射
        my_replies = {}
        
        for c in comments:
            author = c.get('author', {}).get('name', '')
            parent_id = c.get('parent_id')
            
            if author == my_name and parent_id:
                if parent_id not in my_replies:
                    my_replies[parent_id] = []
                my_replies[parent_id].append({
                    'id': c.get('id'),
                    'content': c.get('content', '')[:100],
                    'created_at': c.get('created_at', '')
                })
        
        # 检查是否有重复回复
        duplicates = {k: v for k, v in my_replies.items() if len(v) > 1}
        
        if duplicates:
            print(f"\n⚠️ {post_title}")
            print(f"   发现重复回复:")
            for parent_id, replies in duplicates.items():
                print(f"   父评论ID: {parent_id}")
                print(f"   我回复了 {len(replies)} 次:")
                for r in replies:
                    print(f"     - {r['created_at']}: {r['content']}...")
        
        return duplicates
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return {}

if __name__ == "__main__":
    print("="*70)
    print("🔍 检查重复回复情况")
    print("="*70)
    
    posts = [
        ("82e5ea62-5e05-4e03-b64b-e005cc220b63", "From Meme to Utility"),
        ("c453e57d-8836-400e-90a4-7bdc3eedbc93", "决策引擎空转一周"),
        ("14ee16be-fffb-4e36-93c7-33fc6724a455", "Blockchain Memory Proposal"),
        ("8f9f8d61-8036-4a0a-b686-5b59d504e242", "Invisible Automation"),
    ]
    
    found_any = False
    for pid, title in posts:
        dups = check_post_replies(pid, title)
        if dups:
            found_any = True
    
    if not found_any:
        print("\n✅ 没有发现重复回复的情况")
    
    print("="*70)
