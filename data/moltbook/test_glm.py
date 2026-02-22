#!/usr/bin/env python3
"""测试GLM API调用"""

import requests
import re

# 读取API key
try:
    with open('/root/.openclaw/workspace/TOOLS.md', 'r') as f:
        content = f.read()
        match = re.search(r'NVIDIA Build API: (nvapi-[a-zA-Z0-9]+)', content)
        if match:
            api_key = match.group(1)
            print(f"✅ 找到API Key: {api_key[:20]}...")
        else:
            print("❌ 未找到API Key")
            exit(1)
except Exception as e:
    print(f"❌ 读取失败: {e}")
    exit(1)

# 测试GLM调用
print("\n🤖 测试GLM-4 API...")

try:
    resp = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "nvidia-build/z-ai/glm4.7",
            "messages": [
                {"role": "system", "content": "你是AI Agent开发者"},
                {"role": "user", "content": "请简短回复：什么是Agent的主动式自动化？"}
            ],
            "temperature": 0.7,
            "max_tokens": 200
        },
        timeout=30
    )
    
    if resp.status_code == 200:
        result = resp.json()
        reply = result['choices'][0]['message']['content']
        print(f"\n✅ GLM调用成功！")
        print(f"\n回复内容:\n{reply}")
    else:
        print(f"❌ API错误: {resp.status_code}")
        print(f"响应: {resp.text[:500]}")
        
except Exception as e:
    print(f"❌ 调用失败: {e}")
