#!/usr/bin/env python3
"""
网页情报收集简化版 - 快速模式
仅提取列表页，不访问详情页
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "web-extractor"))

from generic_extractor import GenericExtractor


async def collect_intel_fast():
    """快速收集多平台情报（仅列表页）"""
    print(f"\n{'='*60}")
    print(f"🌐 网页情报收集(快速模式) - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    intel_dir = Path("memory/intel")
    intel_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # 1. Moltbook 热门
    print("📊 [1/3] 收集 Moltbook 热门帖子...")
    try:
        from moltbook_extractor import MoltbookExtractor
        extractor = MoltbookExtractor()
        items = await extractor.get_hot_posts(limit=10)
        results['moltbook'] = {
            'count': len(items),
            'top_posts': [
                {
                    'title': item.get('title', '无标题')[:100],
                    'author': item.get('author', '未知'),
                    'likes': item.get('likes', 0),
                    'url': item.get('url', '')
                }
                for item in items[:5]
            ]
        }
        print(f"   ✅ 收集 {len(items)} 条")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        results['moltbook'] = {'error': str(e)}
    
    # 2. Hacker News - 使用通用提取器，但不提取详情
    print("\n📰 [2/3] 收集 Hacker News 头条...")
    try:
        hn = GenericExtractor("scripts/web-extractor/configs/hackernews.json")
        # 覆盖配置，不提取详情页
        hn.config['detail_page']['enabled'] = False
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
    
    # 3. GitHub Trending - 不提取详情
    print("\n🐙 [3/3] 收集 GitHub Trending...")
    try:
        github = GenericExtractor("scripts/web-extractor/configs/github_trending.json")
        github.config['detail_page']['enabled'] = False
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
        "cost": "0 tokens (local execution)",
        "mode": "fast (no detail pages)"
    }
    
    with open(intel_file, 'w', encoding='utf-8') as f:
        json.dump(intel_summary, f, ensure_ascii=False, indent=2)
    
    # 同时生成Markdown摘要
    md_file = intel_dir / f"intel_summary_{timestamp}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# 🌐 网页情报摘要 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**收集时间**: {datetime.now().isoformat()}\n")
        f.write(f"**成本**: 0 tokens (纯本地执行)\n\n")
        
        # Moltbook
        f.write("## 📊 Moltbook 热门帖子\n\n")
        if 'top_posts' in results.get('moltbook', {}):
            for i, post in enumerate(results['moltbook']['top_posts'], 1):
                f.write(f"{i}. **{post['title']}**\n")
                f.write(f"   - 作者: {post.get('author', '未知')} | 👍 {post.get('likes', 0)}\n\n")
        else:
            f.write(f"错误: {results.get('moltbook', {}).get('error', '未知错误')}\n\n")
        
        # Hacker News
        f.write("## 📰 Hacker News 头条\n\n")
        if 'top_posts' in results.get('hackernews', {}):
            for i, post in enumerate(results['hackernews']['top_posts'], 1):
                f.write(f"{i}. **{post['title']}**\n")
                f.write(f"   - 分数: {post.get('score', 'N/A')} | [链接]({post.get('url', '')})\n\n")
        else:
            f.write(f"错误: {results.get('hackernews', {}).get('error', '未知错误')}\n\n")
        
        # GitHub
        f.write("## 🐙 GitHub Trending\n\n")
        if 'top_repos' in results.get('github_trending', {}):
            for i, repo in enumerate(results['github_trending']['top_repos'], 1):
                f.write(f"{i}. **{repo['name']}**\n")
                f.write(f"   - 语言: {repo.get('language', 'N/A')} | ⭐ {repo.get('stars', 'N/A')}\n\n")
        else:
            f.write(f"错误: {results.get('github_trending', {}).get('error', '未知错误')}\n\n")
    
    # 输出摘要
    print(f"\n{'='*60}")
    print("📋 情报收集摘要")
    print(f"{'='*60}")
    print(f"Moltbook:     {results.get('moltbook', {}).get('count', 0)} 条")
    print(f"Hacker News:  {results.get('hackernews', {}).get('count', 0)} 条")
    print(f"GitHub Trend: {results.get('github_trending', {}).get('count', 0)} 条")
    print(f"\n💾 JSON: {intel_file}")
    print(f"📝 Markdown: {md_file}")
    print(f"💰 成本: 0 tokens")
    print(f"{'='*60}\n")
    
    return intel_summary


if __name__ == "__main__":
    result = asyncio.run(collect_intel_fast())
