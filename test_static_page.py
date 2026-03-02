#!/usr/bin/env python3
"""测试简单静态网页提取"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/tools')
from web_extractor import WebExtractor

async def test_simple_page():
    """测试简单静态网页提取"""
    extractor = WebExtractor(headless=True)

    # 测试提取 Python 文档（静态页面）
    test_url = "https://docs.python.org/3/tutorial/index.html"

    print(f"🔍 测试提取: {test_url}")

    content = await extractor.extract_page(test_url)

    print(f"\n📊 提取结果:")
    print(f"   标题: {content.title}")
    print(f"   段落数: {len(content.paragraphs)}")
    print(f"   标题数: {len(content.headings)}")
    print(f"   链接数: {len(content.links)}")

    if content.paragraphs:
        print(f"\n   前3个段落标题:")
        for i, (head, para) in enumerate(zip(content.paragraphs[:3], content.paragraphs[:3]), 1):
            print(f"   [{i}] {para[:100]}...")

    return len(content.paragraphs) > 0

if __name__ == "__main__":
    success = asyncio.run(test_simple_page())
    print(f"\n{'✅ 测试成功' if success else '❌ 测试失败'}")
