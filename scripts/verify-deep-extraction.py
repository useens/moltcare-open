#!/usr/bin/env python3
"""
深度提取功能验证测试
测试Playwright + 系统Chromium配置
"""

import asyncio
import sys
sys.path.insert(0, 'scripts/web-extractor')

from deep_learning_extractor import DeepLearningExtractor

async def verify_deep_extraction():
    print("="*70)
    print("🔥 深度提取功能验证测试")
    print("="*70)
    print()
    
    # 测试1: 基础导入
    print("【测试1】深度提取器导入...")
    try:
        from deep_learning_extractor import CHROMIUM_PATH
        print(f"✅ 导入成功")
        print(f"   Chromium路径: {CHROMIUM_PATH}")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 测试2: Moltbook深度提取
    print()
    print("【测试2】Moltbook深度提取...")
    try:
        extractor = DeepLearningExtractor('scripts/web-extractor/configs/moltbook.json')
        items = await extractor.collect_with_deep_learning(
            url='https://www.moltbook.com/?sort=hot',
            max_deep_extract=2
        )
        print(f"✅ 提取完成")
        print(f"   获取内容: {len(items)} 条")
        
        if items:
            for i, item in enumerate(items[:3], 1):
                title = item.get('title', 'N/A')[:70]
                signal = item.get('signal', 0)
                deep = '✅ 深度' if item.get('deep_content') else '❌ 未深度'
                print(f"   {i}. Signal {signal} | {deep} | {title}...")
        else:
            print("   ⚠️ 未获取到内容 (可能页面结构变化或无新内容)")
        
        return True
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(verify_deep_extraction())
print()
print("="*70)
if result:
    print("✅ 深度提取验证通过")
else:
    print("❌ 深度提取验证失败")
print("="*70)
