#!/usr/bin/env python3
"""
NVIDIA Build 模型快速测试
验证配置的模型是否可用
"""

import os
import sys
import requests
import json

# API配置
API_KEY = os.getenv("NVIDIA_API_KEY", "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")
BASE_URL = "https://integrate.api.nvidia.com/v1"

# 测试模型
MODELS = [
    "moonshotai/kimi-k2.5",
    "z-ai/glm4.7",
    "stepfun-ai/step-3.5-flash"
]

def test_model(model_id):
    """测试单个模型"""
    print(f"\n🧪 测试模型: {model_id}")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_id,
        "messages": [
            {"role": "user", "content": "你好，请回复'模型测试成功'"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ 成功 | 响应: {content[:50]}...")
            return True
        else:
            print(f"❌ 失败 | HTTP {response.status_code}: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ 错误 | {str(e)}")
        return False

def main():
    print("=" * 50)
    print("NVIDIA Build 模型测试")
    print("=" * 50)
    
    results = []
    for model in MODELS:
        results.append((model, test_model(model)))
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for model, success in results:
        status = "✅ 可用" if success else "❌ 失败"
        print(f"{status} | {model}")
    
    # 统计
    success_count = sum(1 for _, s in results if s)
    print(f"\n总计: {success_count}/{len(MODELS)} 个模型可用")
    
    return 0 if success_count == len(MODELS) else 1

if __name__ == "__main__":
    sys.exit(main())
