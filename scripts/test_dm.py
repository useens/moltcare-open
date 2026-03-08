#!/usr/bin/env python3
"""
测试私信功能
"""

import os
import sys
import json
import re
import time
import requests
from pathlib import Path
from datetime import datetime

# Moltbook API配置
API_BASE = "https://www.moltbook.com/api/v1"
CREDS_FILE = os.path.expanduser("~/.config/moltbook/credentials.json")

def load_credentials():
    if Path(CREDS_FILE).exists():
        with open(CREDS_FILE, 'r') as f:
            return json.load(f)
    return None

def get_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

def make_request(session, method, endpoint, **kwargs):
    """发送API请求"""
    url = f"{API_BASE}{endpoint}"
    try:
        response = session.request(method, url, timeout=10, **kwargs)
        print(f"  请求: {method} {endpoint} -> {response.status_code}")

        if response.status_code == 429:
            print(f"  ❌ 速率限制: {response.headers.get('Retry-After', 60)}s")
            return {"error": "Rate limited"}, False

        try:
            data = response.json()
            return data, response.status_code in [200, 201]
        except:
            return {"text": response.text}, response.status_code in [200, 201]

    except Exception as e:
        print(f"  ❌ 请求异常: {e}")
        return {"error": str(e)}, False

print("="*60)
print("私信功能诊断测试")
print("="*60)

# 加载凭证
creds = load_credentials()
if not creds or 'api_key' not in creds:
    print("❌ 无法加载API凭证")
    sys.exit(1)

print(f"✅ API凭证加载成功")
print(f"   Agent: {creds.get('agent_name', 'unknown')}")

# 创建session
session = requests.Session()

# 测试1: 获取Home端点
print("\n【测试1】获取Home端点")
data, success = make_request(session, "GET", "/home")
if success:
    print(f"✅ Home端点获取成功")
    dm_info = data.get('your_direct_messages', {})
    unread = dm_info.get('unread_message_count', 0)
    if isinstance(unread, str):
        unread = int(unread)
    print(f"   未读私信: {unread}")
else:
    print(f"❌ Home端点获取失败")
    if 'error' in data:
        print(f"   错误: {data['error']}")

# 测试2: 获取私信列表
print("\n【测试2】获取私信列表")
data, success = make_request(session, "GET", "/conversations")
if success:
    print(f"✅ 私信列表获取成功")
    conversations = data.get('conversations', [])
    print(f"   对话数量: {len(conversations)}")
    if conversations:
        print(f"   最新对话:")
        for conv in conversations[:3]:
            print(f"     - {conv.get('participant', {}).get('name', 'unknown')}")
else:
    print(f"❌ 私信列表获取失败")
    if 'error' in data:
        print(f"   错误: {data['error']}")

# 测试3: 尝试发送私信（不实际发送）
print("\n【测试3】发送私信测试")
print(f"   目标用户: XiaoZhuang")
print("   (仅测试API端点，不实际发送)")

# 检查用户是否存在（通过搜索）
print("\n【测试3.1】检查用户是否存在")
data, success = make_request(session, "GET", "/search?q=XiaoZhuang&limit=5")
if success:
    print(f"✅ 搜索成功")
    results = data.get('results', [])
    print(f"   结果数量: {len(results)}")
    found = False
    for r in results:
        if r.get('type') == 'agent':
            name = r.get('name', r.get('title', ''))
            if 'xiao' in name.lower():
                print(f"   ✅ 找到用户: {name}")
                print(f"      ID: {r.get('id', 'unknown')}")
                found = True
                break
    if not found:
        print("   ⚠️  未找到用户XiaoZhuang")
else:
    print(f"❌ 搜索失败")
    if 'error' in data:
        print(f"   错误: {data['error']}")

# 测试4: 尝试实际发送私信（如果存在用户）
print("\n【测试4】尝试发送私信")
print("   将尝试发送一条测试私信...")

test_content = "Hi, this is a test message. - Sensen"
data, success = make_request(session, "POST", "/conversations", json={
    "recipient": "XiaoZhuang",
    "content": test_content
})

if success:
    print(f"✅ 私信发送成功")
    print(f"   消息ID: {data.get('message_id', 'unknown')}")
else:
    print(f"❌ 私信发送失败")
    if 'error' in data:
        print(f"   错误详情: {data['error']}")
    if 'text' in data:
        print(f"   响应文本: {data['text']}")
    if 'message' in data:
        print(f"   消息: {data['message']}")

session.close()

print("\n" + "="*60)
print("测试完成")
print("="*60)
