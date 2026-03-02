#!/usr/bin/env python3
"""测试真实的 Web 搜索"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/tools')
from web_extractor import WebExtractor

async def test_real_search():
    """测试真实的搜索功能"""
    extractor = WebExtractor(headless=True)

    # 测试搜索
    print("🔍 测试真实搜索...")
    results = await extractor.search_google("agent memory systems", num_results=3)

    print(f"\n📊 结果统计: {len(results)} 条")

    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result.title}")
        print(f"   URL: {result.url}")
        print(f"   来源: {result.source}")
        print(f"   摘要: {result.snippet[:100]}...")

    return len(results) > 0

if __name__ == "__main__":
    success = asyncio.run(test_real_search())
    print(f"\n{'✅ 测试成功' if success else '❌ 测试失败'}")
