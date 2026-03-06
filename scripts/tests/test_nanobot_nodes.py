#!/usr/bin/env python3
"""测试10个Nanobot节点的API和对话功能"""

import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "z-ai/glm4.7"

API_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]

def test_node(node_idx, api_key):
    """测试单个节点"""
    node_name = f"NB{node_idx+1:02d}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 测试1: API连通性
    try:
        resp = requests.get(f"{BASE_URL}/models", headers=headers, timeout=10)
        if resp.status_code != 200:
            return (node_name, "❌", f"API连通性失败 (HTTP {resp.status_code})")
    except Exception as e:
        return (node_name, "❌", f"API连通性异常: {str(e)[:30]}")
    
    # 测试2: 对话功能
    try:
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": f"Test from {node_name}"}],
            "max_tokens": 20
        }
        resp = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                return (node_name, "✅", "对话功能正常")
            else:
                return (node_name, "🟡", "响应为空")
        elif resp.status_code == 429:
            return (node_name, "⚠️", "速率限制")
        else:
            return (node_name, "❌", f"对话失败 (HTTP {resp.status_code})")
    except Exception as e:
        return (node_name, "❌", f"对话异常: {str(e)[:30]}")

def main():
    print("测试10个Nanobot节点...")
    print("=" * 50)
    
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(test_node, i, key): i 
            for i, key in enumerate(API_KEYS)
        }
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"{result[0]}: {result[1]} {result[2]}")
    
    # 排序并汇总
    results.sort(key=lambda x: x[0])
    print("=" * 50)
    
    success = sum(1 for r in results if r[1] == "✅")
    rate_limit = sum(1 for r in results if r[1] == "⚠️")
    failed = sum(1 for r in results if r[1] == "❌")
    
    print(f"\n汇总:")
    print(f"  ✅ 正常: {success}/10")
    print(f"  ⚠️  速率限制: {rate_limit}/10")
    print(f"  ❌ 失败: {failed}/10")
    
    if success == 10:
        print("\n🎉 所有节点测试通过！")
    elif success >= 7:
        print(f"\n✓ 大部分节点可用 ({success}/10)")
    else:
        print(f"\n⚠️ 多个节点存在问题")

if __name__ == "__main__":
    main()
