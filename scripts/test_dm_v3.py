#!/usr/bin/env python3
"""
简单测试是否可以找到XiaoZhuang用户
"""

import os
import sys
import json
import requests
from pathlib import Path

API_BASE = "https://www.moltbook.com/api/v1"
CREDS_FILE = os.path.expanduser("~/.config/moltbook/credentials.json")

def load_credentials():
    if Path(CREDS_FILE).exists():
        with open(CREDS_FILE, 'r') as f:
            return json.load(f)
    return None

creds = load_credentials()
session = requests.Session()

print("搜索XiaoZhuang...")
response = session.get(f"{API_BASE}/search?q=XiaoZhuang&limit=10", timeout=10)
print(f"状态码: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"总结果数: {len(data.get('results', []))}")

    for i, r in enumerate(data.get('results', [])):
        print(f"\n结果 {i+1}:")
        print(f"  类型: {r.get('type')}")
        print(f"  标题: {r.get('title')}")
        print(f"  ID: {r.get('id')}")

        if 'author' in r:
            print(f"  作者: {r.get('author', {}).get('name')}")

        # 检查是否是Agent
        if r.get('type') == 'agent':
            name = r.get('name', r.get('title', ''))
            print(f"  Agent名称: {name}")
            if 'xiao' in name.lower():
                print(f"  ✅ 这就是XiaoZhuang!")
                print(f"  ID: {r.get('id')}")
