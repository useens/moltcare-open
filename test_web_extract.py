#!/usr/bin/env python3
"""测试真实的网页提取"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/tools')
from web_extractor import WebExtractor

async def test_extraction():
    """测试网页提取功能"""
    extractor = WebExtractor(headless=True)

    # 测试提取 Moltbook 帖子
    test_url = "https://www.moltbook.com/post/e6dd27c6-4e87-422a-a7c9-bcb6381cb484"

    print(f"🔍 测试提取: {test_url}")

    content = await extractor.extract_page(test_url)

    print(f"\n📊 提取结果:")
    print(f"   标题: {content.title}")
    print(f"   段落数: {len(content.paragraphs)}")
    print(f"   标题数: {len(content.headings)}")
    print(f"   链接数: {len(content.links)}")

    if content.paragraphs:
        print(f"\n   第一段内容预览:")
        print(f"   {content.paragraphs[0][:200]}...")

    return len(content.paragraphs) > 0

if __name__ == "__main__":
    success = asyncio.run(test_extraction())
    print(f"\n{'✅ 测试成功' if success else '❌ 测试失败'}")
