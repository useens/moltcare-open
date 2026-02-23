#!/usr/bin/env python3
"""
$MOLT帖子监控 - 使用API获取评论
每15分钟检查一次，有新评论时使用真实AI回复
"""

import json
import requests
from pathlib import Path
from datetime import datetime

# 配置
POST_ID = "8564da6f-23c2-45b7-a3ba-3e315a6b0a53"
REPLIED_FILE = "/root/.openclaw/workspace/data/moltbook/molt-replied-comments.json"

# 加载凭证
creds_file = Path("/root/.config/moltbook/credentials.json")
with open(creds_file) as f:
    creds = json.load(f)

headers = {
    "Authorization": f"Bearer {creds['api_key']}",
    "Content-Type": "application/json"
}

def load_replied():
    """加载已回复的评论ID"""
    try:
        with open(REPLIED_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_replied(replied):
    """保存已回复的评论ID"""
    with open(REPLIED_FILE, 'w') as f:
        json.dump(replied, f, indent=2)

def get_comments():
    """使用API获取评论"""
    try:
        resp = requests.get(
            f"https://www.moltbook.com/api/v1/posts/{POST_ID}/comments",
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get('comments', [])
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    print(f"[{datetime.now()}] 监控$MOLT帖子评论...")
    
    comments = get_comments()
    replied = load_replied()
    
    new_comments = []
    for c in comments:
        cid = c.get('id')
        author = c.get('author', {}).get('name', '')
        if cid not in replied and author != 'novaassistantpro':
            new_comments.append(c)
    
    print(f"  总评论: {len(comments)}")
    print(f"  新评论: {len(new_comments)}")
    
    if new_comments:
        print(f"\n发现 {len(new_comments)} 条新评论，请手动处理或触发AI回复")
        for c in new_comments:
            author = c.get('author', {}).get('name', '')
            content = c.get('content', '')[:50]
            print(f"  - @{author}: {content}...")
    else:
        print("  无新评论")
    
    print(f"[{datetime.now()}] 监控完成")

if __name__ == "__main__":
    main()
