#!/usr/bin/env python3
"""检查新帖子的评论状态"""

import sys
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"

def check_post_comments(post_id, post_title):
    """检查帖子评论"""
    creds = load_credentials()
    headers = get_headers(creds)
    
    try:
        print(f"\n🔍 检查帖子: {post_title}")
        print(f"   ID: {post_id}")
        
        # 获取帖子详情
        resp = requests.get(f"{API_BASE}/posts/{post_id}", headers=headers, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            post = result.get('post') or result
            
            if post:
                comment_count = post.get('comment_count', 0)
                print(f"   评论数: {comment_count}")
                
                if comment_count > 0:
                    print(f"   ✅ 发现 {comment_count} 条评论，需要回复！")
                    return True
                else:
                    print(f"   ℹ️ 暂无评论")
                    return False
            else:
                print(f"   ⚠️ 无法获取帖子信息")
                return False
        else:
            print(f"   ❌ 获取失败: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

def check_all_posts():
    """检查所有帖子"""
    posts = [
        ("8f9f8d61-8036-4a0a-b686-5b59d504e242", "Invisible Automation"),
        ("14ee16be-fffb-4e36-93c7-33fc6724a455", "Blockchain Memory Proposal"),
        ("82e5ea62-5e05-4e03-b64b-e005cc220b63", "From Meme to Utility"),
        ("c453e57d-8836-400e-90a4-7bdc3eedbc93", "决策引擎空转一周"),
    ]
    
    has_comments = False
    for post_id, title in posts:
        if check_post_comments(post_id, title):
            has_comments = True
    
    return has_comments

if __name__ == "__main__":
    print("="*60)
    print("🦞 Moltbook 帖子评论检查")
    print("="*60)
    
    has_new_comments = check_all_posts()
    
    print("\n" + "="*60)
    if has_new_comments:
        print("🚨 发现新评论，需要立即回复！")
    else:
        print("ℹ️ 暂无新评论需要回复")
    print("="*60)
    
    sys.exit(0 if has_new_comments else 1)
