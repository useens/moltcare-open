#!/usr/bin/env python3
"""
生态扫描绝对诚实验证测试
"""

import asyncio
import sys
import os
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/usr/bin/chromium'
os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'
sys.path.insert(0, 'scripts/web-extractor')

from deep_learning_extractor import DeepLearningExtractor

async def test_scan():
    print("🔍 测试HackerNews深度提取...")
    try:
        extractor = DeepLearningExtractor('scripts/web-extractor/configs/hackernews.json')
        items = await extractor.collect_with_deep_learning(max_deep_extract=1)
        print(f"✅ 测试成功! 获取 {len(items)} 条内容")
        if items:
            for i, item in enumerate(items[:2], 1):
                title = item.get('title', 'N/A')[:60]
                signal = item.get('signal', 0)
                print(f"  {i}. Signal {signal} | {title}...")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(test_scan())
status = "✅ 通过" if result else "❌ 失败"
print(f"\n{'='*60}")
print(f"生态扫描验证: {status}")
print(f"{'='*60}")
