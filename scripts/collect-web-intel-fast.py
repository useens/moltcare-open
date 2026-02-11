#!/usr/bin/env python3
"""
轻量进化 v2.0 - 深度学习模式
不只是标题，要点进去看完整内容
Signal > 7 必须深度提取
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "web-extractor"))

from deep_learning_extractor import DeepLearningExtractor


def calculate_signal(item: dict) -> int:
    """计算内容Signal评分 (1-10)"""
    score = 5  # 基础分
    
    # 根据点赞/分数加分
    likes = item.get('likes', 0) or item.get('score', 0) or item.get('stars', 0)
    if isinstance(likes, str):
        likes = int(likes.replace('k', '000').replace('.', '')) if 'k' in likes.lower() else int(likes)
    
    if likes > 1000:
        score += 3
    elif likes > 500:
        score += 2
    elif likes > 100:
        score += 1
    
    # 根据标题关键词加分
    title = item.get('title', '').lower()
    high_signal_keywords = [
        'agent', 'llm', 'ai', 'memory', 'autonomous', 'evolution',
        'mcp', 'rag', 'vector', 'embedding', 'learning'
    ]
    for keyword in high_signal_keywords:
        if keyword in title:
            score += 1
            break
    
    return min(score, 10)


async def deep_learning_evolution():
    """深度学习闭环进化"""
    print(f"\n{'='*60}")
    print(f"🧬 轻量进化 v2.0 (深度学习模式) - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    intel_dir = Path("memory/intel")
    intel_dir.mkdir(parents=True, exist_ok=True)
    
    learning_debt_file = Path("memory/learning-debt.md")
    
    results = {
        'moltbook': {'scanned': 0, 'deep_extracted': 0, 'high_signal': []},
        'hackernews': {'scanned': 0, 'deep_extracted': 0, 'high_signal': []},
        'github': {'scanned': 0, 'deep_extracted': 0, 'high_signal': []}
    }
    
    # 1. Moltbook - 深度学习
    print("📊 [1/3] Moltbook 深度学习...")
    try:
        extractor = DeepLearningExtractor("scripts/web-extractor/configs/moltbook.json")
        items = await extractor.collect_with_deep_learning(
            url="https://www.moltbook.com/?sort=hot",
            max_deep_extract=3  # 最多深度提取3条高Signal内容
        )
        
        for item in items:
            results['moltbook']['scanned'] += 1
            signal = calculate_signal(item)
            item['signal'] = signal
            
            if signal >= 7:
                results['moltbook']['high_signal'].append(item)
                if item.get('deep_content'):
                    results['moltbook']['deep_extracted'] += 1
                    print(f"   🔥 Signal {signal}: {item['title'][:60]}...")
        
        print(f"   ✅ 扫描 {results['moltbook']['scanned']} 条, 深度提取 {results['moltbook']['deep_extracted']} 条")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 2. Hacker News - 深度学习
    print("\n📰 [2/3] Hacker News 深度学习...")
    try:
        extractor = DeepLearningExtractor("scripts/web-extractor/configs/hackernews.json")
        items = await extractor.collect_with_deep_learning(
            max_deep_extract=3
        )
        
        for item in items:
            results['hackernews']['scanned'] += 1
            signal = calculate_signal(item)
            item['signal'] = signal
            
            if signal >= 7:
                results['hackernews']['high_signal'].append(item)
                if item.get('deep_content'):
                    results['hackernews']['deep_extracted'] += 1
                    print(f"   🔥 Signal {signal}: {item['title'][:60]}...")
        
        print(f"   ✅ 扫描 {results['hackernews']['scanned']} 条, 深度提取 {results['hackernews']['deep_extracted']} 条")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 3. GitHub Trending - 深度学习
    print("\n🐙 [3/3] GitHub Trending 深度学习...")
    try:
        extractor = DeepLearningExtractor("scripts/web-extractor/configs/github_trending.json")
        items = await extractor.collect_with_deep_learning(
            max_deep_extract=3
        )
        
        for item in items:
            results['github']['scanned'] += 1
            signal = calculate_signal(item)
            item['signal'] = signal
            
            if signal >= 7:
                results['github']['high_signal'].append(item)
                if item.get('deep_content'):
                    results['github']['deep_extracted'] += 1
                    print(f"   🔥 Signal {signal}: {item['title'][:60]}...")
        
        print(f"   ✅ 扫描 {results['github']['scanned']} 条, 深度提取 {results['github']['deep_extracted']} 条")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 保存情报
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    intel_file = intel_dir / f"intel_deep_{timestamp}.json"
    
    # 只保存高Signal内容
    high_signal_items = (
        results['moltbook']['high_signal'] +
        results['hackernews']['high_signal'] +
        results['github']['high_signal']
    )
    
    intel_summary = {
        "collection_time": datetime.now().isoformat(),
        "mode": "deep_learning",
        "total_scanned": sum(r['scanned'] for r in results.values()),
        "total_deep_extracted": sum(r['deep_extracted'] for r in results.values()),
        "high_signal_count": len(high_signal_items),
        "high_signal_items": high_signal_items,
        "learning_debt_added": len(high_signal_items)  # 高Signal内容加入学习债务
    }
    
    with open(intel_file, 'w', encoding='utf-8') as f:
        json.dump(intel_summary, f, ensure_ascii=False, indent=2)
    
    # 更新学习债务
    if high_signal_items:
        with open(learning_debt_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} - 轻量进化高Signal内容\n\n")
            for item in high_signal_items:
                f.write(f"- [Signal {item['signal']}] [{item['title'][:80]}]({item.get('url', '')})\n")
                if item.get('deep_content'):
                    f.write(f"  - 已深度提取: {len(item['deep_content'])} 字符\n")
            f.write(f"\n待处理: {len(high_signal_items)} 条\n")
    
    # 输出摘要
    print(f"\n{'='*60}")
    print("📋 深度学习摘要")
    print(f"{'='*60}")
    print(f"总扫描:     {intel_summary['total_scanned']} 条")
    print(f"高Signal:   {intel_summary['high_signal_count']} 条 (>=7)")
    print(f"深度提取:   {intel_summary['total_deep_extracted']} 条")
    print(f"学习债务:   +{intel_summary['learning_debt_added']} 条")
    print(f"💾 保存至:   {intel_file}")
    print(f"{'='*60}\n")
    
    return intel_summary


if __name__ == "__main__":
    result = asyncio.run(deep_learning_evolution())
