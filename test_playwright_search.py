#!/usr/bin/env python3
"""测试 Playwright 搜索"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

from autonomous_decision_engine import DecisionEngine

def test_playwright_search():
    """测试 Playwright 搜索"""
    engine = DecisionEngine()

    # 测试搜索
    query = "agent memory systems"
    print(f"🔍 测试搜索: {query}")

    results = engine._do_web_search_playwright(query, max_results=3)

    print(f"\n📊 结果统计: {len(results)} 条")

    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   来源: {result['source']}")
        print(f"   摘要: {result['snippet'][:100] if result.get('snippet') else 'N/A'}...")

    return len(results) > 0

if __name__ == "__main__":
    success = test_playwright_search()
    print(f"\n{'✅ 测试成功' if success else '❌ 测试失败'}")
