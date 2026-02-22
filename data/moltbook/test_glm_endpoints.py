#!/usr/bin/env python3
"""测试GLM API调用 - 尝试不同端点"""

import requests
import re

# 读取API key
try:
    with open('/root/.openclaw/workspace/TOOLS.md', 'r') as f:
        content = f.read()
        match = re.search(r'NVIDIA Build API: (nvapi-[a-zA-Z0-9\.]+)', content)
        if match:
            api_key = match.group(1)
            print(f"✅ 找到API Key: {api_key[:25]}...")
        else:
            print("❌ 未找到API Key")
            exit(1)
except Exception as e:
    print(f"❌ 读取失败: {e}")
    exit(1)

# 尝试不同端点
endpoints = [
    "https://integrate.api.nvidia.com/v1/chat/completions",
    "https://api.nvidia.com/v1/chat/completions",
    "https://build.nvidia.com/v1/chat/completions",
]

for endpoint in endpoints:
    print(f"\n🤖 测试: {endpoint}")
    try:
        resp = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "nvidia-build/z-ai/glm4.7",
                "messages": [
                    {"role": "user", "content": "简短回答：什么是Agent？"}
                ],
                "max_tokens": 100
            },
            timeout=10
        )
        
        print(f"   状态: {resp.status_code}")
        if resp.status_code == 200:
            print(f"   ✅ 成功！")
            print(f"   回复: {resp.json()['choices'][0]['message']['content'][:100]}")
            break
        else:
            print(f"   错误: {resp.text[:200]}")
            
    except Exception as e:
        print(f"   异常: {e}")
