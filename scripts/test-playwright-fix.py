#!/usr/bin/env python3
"""
Playwright修复验证测试
"""

import asyncio
import sys
sys.path.insert(0, 'scripts/web-extractor')

from deep_learning_extractor import DeepLearningExtractor

async def final_test():
    try:
        print('🔍 最终验证: Moltbook深度提取...')
        extractor = DeepLearningExtractor('scripts/web-extractor/configs/moltbook.json')
        items = await extractor.collect_with_deep_learning(
            url='https://www.moltbook.com/?sort=hot',
            max_deep_extract=1
        )
        print(f'✅ 验证成功! 获取 {len(items)} 条内容')
        if items:
            title = items[0].get('title', 'N/A')[:60]
            print(f'   第一条: {title}...')
        return True
    except Exception as e:
        print(f'❌ 验证失败: {e}')
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(final_test())
status = "✅ 通过" if result else "❌ 失败"
print(f'\n验证结果: {status}')
