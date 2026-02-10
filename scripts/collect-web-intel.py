#!/usr/bin/env python3
"""
网页情报收集自动化脚本
每天04:00执行，收集多平台情报
零Token消耗，纯本地执行
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "web-extractor"))

from generic_extractor import GenericExtractor


async def collect_intel():
    """收集多平台情报"""
    print(f"\n{'='*60}")
    print(f"🌐 网页情报收集 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    intel_dir = Path("memory/intel")
    intel_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # 1. Moltbook 热门
    print("📊 [1/3] 收集 Moltbook 热门帖子...")
    try:
        moltbook = GenericExtractor("scripts/web-extractor/configs/moltbook.json")
        moltbook_items = await moltbook.run(
            url="https://www.moltbook.com/?sort=hot",
            mode="list"
        )
        results['moltbook'] = {
            'count': len(moltbook_items),
            'top_posts': [
                {
                    'title': item.get('title', '无标题')[:100],
                    'url': item.get('url', '')
                }
                for item in moltbook_items[:5]
            ]
        }
        print(f"   ✅ 收集 {len(moltbook_items)} 条")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        results['moltbook'] = {'error': str(e)}
    
    # 2. Hacker News
    print("\n📰 [2/3] 收集 Hacker News 头条...")
    try:
        hn = GenericExtractor("scripts/web-extractor/configs/hackernews.json")
        hn_items = await hn.run(mode="list")
        results['hackernews'] = {
            'count': len(hn_items),
            'top_posts': [
                {
                    'title': item.get('title', '无标题')[:100],
                    'url': item.get('url', ''),
                    'score': item.get('score', '0')
                }
                for item in hn_items[:5]
            ]
        }
        print(f"   ✅ 收集 {len(hn_items)} 条")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        results['hackernews'] = {'error': str(e)}
    
    # 3. GitHub Trending
    print("\n🐙 [3/3] 收集 GitHub Trending...")
    try:
        github = GenericExtractor("scripts/web-extractor/configs/github_trending.json")
        gh_items = await github.run(mode="list")
        results['github_trending'] = {
            'count': len(gh_items),
            'top_repos': [
                {
                    'name': item.get('title', '无名')[:50],
                    'url': item.get('url', ''),
                    'language': item.get('language', 'N/A'),
                    'stars': item.get('stars', '0')
                }
                for item in gh_items[:5]
            ]
        }
        print(f"   ✅ 收集 {len(gh_items)} 条")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        results['github_trending'] = {'error': str(e)}
    
    # 保存情报摘要
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    intel_file = intel_dir / f"intel_{timestamp}.json"
    
    intel_summary = {
        "collection_time": datetime.now().isoformat(),
        "total_sources": 3,
        "results": results,
        "cost": "0 tokens (local execution)"
    }
    
    with open(intel_file, 'w', encoding='utf-8') as f:
        json.dump(intel_summary, f, ensure_ascii=False, indent=2)
    
    # 输出摘要
    print(f"\n{'='*60}")
    print("📋 情报收集摘要")
    print(f"{'='*60}")
    print(f"Moltbook:     {results.get('moltbook', {}).get('count', 0)} 条")
    print(f"Hacker News:  {results.get('hackernews', {}).get('count', 0)} 条")
    print(f"GitHub Trend: {results.get('github_trending', {}).get('count', 0)} 条")
    print(f"\n💾 保存至: {intel_file}")
    print(f"💰 成本: 0 tokens")
    print(f"{'='*60}\n")
    
    return intel_summary


if __name__ == "__main__":
    result = asyncio.run(collect_intel())
