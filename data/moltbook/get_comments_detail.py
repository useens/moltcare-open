#!/usr/bin/env python3
"""获取帖子详细评论"""

import sys
import json
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"

def get_comments(post_id, post_title):
    """获取帖子评论"""
    creds = load_credentials()
    headers = get_headers(creds)
    
    try:
        print(f"\n📥 获取评论: {post_title}")
        
        # 获取评论列表
        resp = requests.get(f"{API_BASE}/posts/{post_id}/comments", headers=headers, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            comments = result.get('comments', [])
            
            print(f"   共 {len(comments)} 条评论\n")
            
            for i, comment in enumerate(comments, 1):
                author = comment.get('author', {}).get('name', 'Unknown')
                content = comment.get('content', '')[:200]
                comment_id = comment.get('id', 'N/A')
                
                print(f"   [{i}] @{author}")
                print(f"       ID: {comment_id}")
                print(f"       内容: {content}...")
                print()
            
            return comments
        else:
            print(f"   ❌ 获取失败: {resp.status_code}")
            return []
            
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return []

if __name__ == "__main__":
    print("="*60)
    print("💬 获取评论详情")
    print("="*60)
    
    # 获取两个有评论的帖子
    print("\n" + "="*60)
    print("【帖子1】Invisible Automation")
    print("="*60)
    comments1 = get_comments("8f9f8d61-8036-4a0a-b686-5b59d504e242", "Invisible Automation")
    
    print("\n" + "="*60)
    print("【帖子2】From Meme to Utility")
    print("="*60)
    comments2 = get_comments("82e5ea62-5e05-4e03-b64b-e005cc220b63", "From Meme to Utility")
    
    # 保存到文件供后续处理
    with open('/tmp/moltbook_comments.json', 'w') as f:
        json.dump({
            'invisible_automation': comments1,
            'from_meme_to_utility': comments2
        }, f, indent=2)
    
    print("\n✅ 评论已保存到 /tmp/moltbook_comments.json")
