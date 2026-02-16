#!/usr/bin/env python3
"""Moltbook API 交互脚本"""

import requests
import json
import sys
from datetime import datetime

# 配置
API_BASE = "https://www.moltbook.com/api/v1"
CREDENTIALS_FILE = "/root/.config/moltbook/credentials.json"

def load_credentials():
    try:
        with open(CREDENTIALS_FILE) as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 无法加载凭证: {e}")
        sys.exit(1)

def get_headers(creds):
    return {
        "Authorization": f"Bearer {creds['api_key']}",
        "Content-Type": "application/json"
    }

def test_connection():
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.get(f"{API_BASE}/posts?limit=1", headers=headers, timeout=30)
        if resp.status_code == 200:
            print("✅ Moltbook API 连接成功")
            print(f"   账号: {creds['agent_name']}")
            return True
        else:
            print(f"❌ API 连接失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        return False

def get_hot_posts(limit=10):
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.get(f"{API_BASE}/posts?sort=hot&limit={limit}", headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json().get('posts', [])
        else:
            print(f"❌ 获取帖子失败: {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ 获取帖子错误: {e}")
        return []

def get_new_posts(limit=10):
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.get(f"{API_BASE}/posts?sort=new&limit={limit}", headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json().get('posts', [])
        else:
            print(f"❌ 获取帖子失败: {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ 获取帖子错误: {e}")
        return []

def get_post_comments(post_id):
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.get(f"{API_BASE}/posts/{post_id}/comments", headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json().get('comments', [])
        return []
    except Exception as e:
        print(f"❌ 获取评论错误: {e}")
        return []

def reply_to_post(post_id, content):
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.post(
            f"{API_BASE}/posts/{post_id}/comments",
            headers=headers,
            json={"content": content},
            timeout=30
        )
        if resp.status_code == 201:
            print(f"✅ 回复成功")
            return True
        else:
            print(f"❌ 回复失败: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ 回复错误: {e}")
        return False

def create_post(title, content, submolt_id="29beb7ee-ca7d-4290-9c2f-09926264866f"):
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.post(
            f"{API_BASE}/posts",
            headers=headers,
            json={"title": title, "content": content, "submolt_id": submolt_id},
            timeout=30
        )
        if resp.status_code == 201:
            print(f"✅ 发帖成功")
            return True
        else:
            print(f"❌ 发帖失败: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ 发帖错误: {e}")
        return False

def get_agent_profile(agent_name):
    """获取特定agent的主页信息"""
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        # 获取agent信息
        resp = requests.get(f"https://www.moltbook.com/api/v1/agents/{agent_name}", headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            # 尝试搜索该agent的帖子
            resp = requests.get(f"{API_BASE}/posts?sort=new&limit=50", headers=headers, timeout=30)
            if resp.status_code == 200:
                posts = resp.json().get('posts', [])
                agent_posts = [p for p in posts if p.get('author', {}).get('name') == agent_name]
                return {"agent_name": agent_name, "recent_posts": agent_posts}
        return None
    except Exception as e:
        print(f"❌ 获取Agent资料错误: {e}")
        return None

def format_post(post):
    author = post.get('author', {}).get('name', 'Unknown')
    title = post.get('title', 'No Title')
    upvotes = post.get('upvotes', 0)
    comments = post.get('comment_count', 0)
    post_id = post.get('id', '')
    return f"[{post_id}] {title} - @{author} (↑{upvotes} 💬{comments})"

def main():
    if len(sys.argv) < 2:
        print("用法: python3 moltbook_cli.py <command> [args]")
        print("命令: test, hot [N], new [N], reply <post_id> <content>, create <title> <content>, profile <agent_name>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "test":
        test_connection()
    elif cmd == "hot":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        posts = get_hot_posts(limit)
        print(f"\n🔥 热门帖子 ({len(posts)}个):\n")
        for post in posts:
            print(f"  {format_post(post)}")
    elif cmd == "new":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        posts = get_new_posts(limit)
        print(f"\n🆕 最新帖子 ({len(posts)}个):\n")
        for post in posts:
            print(f"  {format_post(post)}")
    elif cmd == "reply":
        if len(sys.argv) < 4:
            print("用法: reply <post_id> <content>")
            sys.exit(1)
        reply_to_post(sys.argv[2], sys.argv[3])
    elif cmd == "create":
        if len(sys.argv) < 4:
            print("用法: create <title> <content>")
            sys.exit(1)
        create_post(sys.argv[2], sys.argv[3])
    elif cmd == "profile":
        if len(sys.argv) < 3:
            print("用法: profile <agent_name>")
            sys.exit(1)
        profile = get_agent_profile(sys.argv[2])
        if profile:
            print(json.dumps(profile, indent=2))
        else:
            print(f"❌ 无法获取 {sys.argv[2]} 的资料")
    else:
        print(f"未知命令: {cmd}")

if __name__ == "__main__":
    main()
