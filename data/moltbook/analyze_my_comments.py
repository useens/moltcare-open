#!/usr/bin/env python3
"""检查决策引擎帖子下我的评论情况"""

import sys
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"
POST_ID = "c453e57d-8836-400e-90a4-7bdc3eedbc93"

def analyze_comments():
    creds = load_credentials()
    headers = get_headers(creds)
    my_name = "novaassistantpro"
    
    try:
        resp = requests.get(f"{API_BASE}/posts/{POST_ID}/comments", headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"❌ 获取失败: {resp.status_code}")
            return
        
        comments = resp.json().get('comments', [])
        
        print(f"📊 总评论数: {len(comments)}\n")
        
        my_comments = []
        others_comments = []
        
        for c in comments:
            author = c.get('author', {}).get('name', 'Unknown')
            content = c.get('content', '')[:100]
            created_at = c.get('created_at', '')
            
            if author == my_name:
                my_comments.append({
                    'content': content,
                    'time': created_at,
                    'id': c.get('id')
                })
            else:
                others_comments.append({
                    'author': author,
                    'content': content,
                    'time': created_at
                })
        
        print(f"⚠️  我的评论: {len(my_comments)} 条")
        print(f"👥 他人评论: {len(others_comments)} 条\n")
        
        print("="*70)
        print("我的评论列表:")
        print("="*70)
        for i, c in enumerate(my_comments, 1):
            print(f"\n[{i}] {c['time']}")
            print(f"    {c['content']}...")
        
        print("\n" + "="*70)
        print("他人评论列表:")
        print("="*70)
        for i, c in enumerate(others_comments, 1):
            print(f"\n[{i}] @{c['author']} - {c['time']}")
            print(f"    {c['content']}...")
        
        print(f"\n{'='*70}")
        print(f"📈 统计:")
        print(f"   我: {len(my_comments)} 条 ({len(my_comments)/len(comments)*100:.1f}%)")
        print(f"   他人: {len(others_comments)} 条 ({len(others_comments)/len(comments)*100:.1f}%)")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    print("🔍 分析决策引擎帖子评论构成")
    print("="*70)
    analyze_comments()
