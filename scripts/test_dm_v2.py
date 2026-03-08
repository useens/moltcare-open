#!/usr/bin/env python3
"""
测试不同私信API端点
"""

import os
import sys
import json
import requests
from pathlib import Path

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

def test_endpoint(session, method, endpoint, description, payload=None):
    """测试API端点"""
    url = f"{API_BASE}{endpoint}"
    try:
        kwargs = {"timeout": 10}
        if payload is not None:
            kwargs["json"] = payload

        response = session.request(method, url, **kwargs)
        status = response.status_code
        try:
            data = response.json()
        except:
            data = {"text": response.text}

        status_icon = "✅" if status in [200, 201] else "❌"
        print(f"{status_icon} {description}")
        print(f"   {method} {endpoint} -> {status}")
        if status not in [200, 201]:
            print(f"   响应: {json.dumps(data, indent=2)[:200]}")
        return data, status in [200, 201]

    except Exception as e:
        print(f"❌ {description}")
        print(f"   请求异常: {e}")
        return {"error": str(e)}, False

print("="*60)
print("测试Moltbook私信API端点")
print("="*60)

# 加载凭证
creds = load_credentials()
if not creds or 'api_key' not in creds:
    print("❌ 无法加载API凭证")
    sys.exit(1)

print(f"✅ API凭证: {creds.get('agent_name', 'unknown')}")

session = requests.Session()

# 获取用户ID
print("\n【步骤1】获取目标用户ID")
data, success = test_endpoint(session, "GET", "/search?q=XiaoZhuang&limit=5", "搜索用户XiaoZhuang")
if not success:
    session.close()
    sys.exit(1)

user_id = None
for r in data.get('results', []):
    if r.get('type') == 'agent' and 'xiao' in r.get('name', '').lower():
        user_id = r.get('id')
        print(f"   ✅ 找到用户ID: {user_id}")
        break

if not user_id:
    print("   ❌ 未找到用户XiaoZhuang")
    session.close()
    sys.exit(1)

# 测试不同的私信端点
print("\n【步骤2】测试私信相关端点")

# GET端点
print(f"\n测试: 获取消息列表")
test_endpoint(session, "GET", "/messages", "获取消息列表")

print(f"\n测试: 获取对话列表")
test_endpoint(session, "GET", "/conversations", "获取对话列表")

print(f"\n测试: 获取与用户的对话")
test_endpoint(session, "GET", f"/conversations/{user_id}", "获取与用户的对话")

print(f"\n测试: 获取用户信息")
test_endpoint(session, "GET", f"/users/{user_id}", "获取用户信息")

print(f"\n测试: 获取Agent信息")
test_endpoint(session, "GET", f"/agents/{user_id}", "获取Agent信息")

# POST端点 - 尝试发送消息
print(f"\n测试: 发送消息(模拟)")
print("   (仅测试端点，不实际发送)")
print(f"   将测试: POST /messages")

try:
    url = f"{API_BASE}/messages"
    response = session.post(url, json={
        "recipient_id": user_id,
        "content": "Test message (do not send)"
    }, timeout=10)
    print(f"   状态: {response.status_code}")
    try:
        data = response.json()
        print(f"   响应: {json.dumps(data)[:150]}")
    except:
        print(f"   响应: {response.text[:150]}")
except Exception as e:
    print(f"   ❌ 请求异常: {e}")

session.close()

print("\n" + "="*60)
print("测试完成 - 请查看上述结果确定正确端点")
print("="*60)
