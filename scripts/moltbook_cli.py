#!/usr/bin/env python3
"""Moltbook API 交互脚本"""

import requests
import json
import sys
import re
import time
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

def solve_verification_challenge(challenge_text):
    """
    解决验证挑战（数学问题）
    示例: "A] lO^bSt-Er S[wImS aT/ tW]eNn-Tyy..." -> 20 - 5 = 15
    """
    # 清理文本：移除非字母数字字符，保留空格
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', challenge_text)
    cleaned = cleaned.lower()

    # 提取所有数字
    numbers = re.findall(r'\d+', cleaned)

    # 可能是英文数字，尝试转换
    word_to_num = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
        'eighty': 80, 'ninety': 90, 'hundred': 100
    }

    words = cleaned.split()
    for word in words:
        if word in word_to_num and str(word_to_num[word]) not in numbers:
            numbers.append(str(word_to_num[word]))

    if len(numbers) < 2:
        print(f"❌ 无法解析足够的数字: {challenge_text[:60]}...")
        return None

    # 提取运算符
    op = '-'
    if any(w in cleaned for w in ['plus', 'add', 'and']):
        op = '+'
    elif any(w in cleaned for w in ['minus', 'subtract', 'slows', 'less', 'by']):
        op = '-'
    elif any(w in cleaned for w in ['times', 'multiply', 'multiplied']):
        op = '*'
    elif any(w in cleaned for w in ['divided', 'divide']):
        op = '/'

    try:
        num1 = int(numbers[0])
        num2 = int(numbers[1])

        if op == '+':
            result = num1 + num2
        elif op == '-':
            result = num1 - num2
        elif op == '*':
            result = num1 * num2
        elif op == '/':
            result = num1 / num2 if num2 != 0 else 0
        else:
            result = num1 - num2

        return f"{result:.2f}"
    except Exception as e:
        print(f"❌ 计算错误: {e}")
        return None

def submit_verification(verification_code, answer):
    """提交验证答案"""
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.post(
            f"{API_BASE}/verify",
            headers=headers,
            json={"verification_code": verification_code, "answer": answer},
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                print(f"✅ 验证成功")
                return True
            else:
                print(f"❌ 验证失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 验证请求失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 验证错误: {e}")
        return False

def handle_verification_response(resp_data):
    """处理可能包含验证挑战的响应"""
    # 检查是否需要验证
    if resp_data.get('verification_required'):
        verification = resp_data.get('verification', {})
        return process_verification(verification)

    # 检查post对象中的验证
    post_data = resp_data.get('post', {})
    if post_data.get('verification'):
        verification = post_data.get('verification', {})
        return process_verification(verification)

    return True, "无需验证"

def process_verification(verification):
    """处理验证挑战"""
    challenge_text = verification.get('challenge_text', '')
    verification_code = verification.get('verification_code', '')

    if not challenge_text or not verification_code:
        return False, "验证信息不完整"

    print(f"⏳ 需要验证，正在解决...")
    answer = solve_verification_challenge(challenge_text)

    if answer:
        print(f"   挑战: {challenge_text[:60]}...")
        print(f"   答案: {answer}")
        if submit_verification(verification_code, answer):
            return True, "验证成功"
        else:
            return False, "验证提交失败"
    else:
        return False, "无法解析挑战"

def reply_to_post(post_id, content, delay_before=0, auto_verify=True):
    """
    回复帖子，支持速率限制、延迟和自动验证
    """
    if delay_before > 0:
        time.sleep(delay_before)

    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.post(
            f"{API_BASE}/posts/{post_id}/comments",
            headers=headers,
            json={"content": content},
            timeout=30
        )

        if resp.status_code == 200 or resp.status_code == 201:
            data = resp.json()

            # 检查是否需要验证
            if auto_verify and (data.get('verification_required') or 
                               data.get('post', {}).get('verification')):
                success, msg = handle_verification_response(data)
                if success:
                    return True
                else:
                    print(f"❌ {msg}")
                    return False

            if data.get('success') or resp.status_code == 201:
                print(f"✅ 回复成功")
                return True

        if resp.status_code == 429:
            print(f"⏱️  速率限制，跳过")
            return False
        else:
            print(f"❌ 回复失败: {resp.status_code} - {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ 回复错误: {e}")
        return False

def upvote_post(post_id):
    """点赞帖子"""
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.post(
            f"{API_BASE}/posts/{post_id}/upvote",
            headers=headers,
            timeout=30
        )
        if resp.status_code in [200, 201]:
            print(f"✅ 点赞成功")
            return True
        else:
            print(f"❌ 点赞失败: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ 点赞错误: {e}")
        return False

def follow_agent(agent_name):
    """关注一个agent"""
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.post(
            f"{API_BASE}/agents/{agent_name}/follow",
            headers=headers,
            timeout=30
        )
        if resp.status_code in [200, 201]:
            print(f"✅ 关注成功: {agent_name}")
            return True
        else:
            print(f"❌ 关注失败: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ 关注错误: {e}")
        return False

def create_post(title, content, submolt_name="General"):
    creds = load_credentials()
    headers = get_headers(creds)
    try:
        resp = requests.post(
            f"{API_BASE}/posts",
            headers=headers,
            json={"title": title, "content": content, "submolt_name": submolt_name},
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
