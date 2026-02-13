#!/usr/bin/env python3
"""
Moltbook完整深度扫描任务
同时扫描: 热门帖子 + 用户主页 + 热门Agent
"""

import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

from moltbook-super-extractor import MoltbookSuperExtractor, CONFIG

async def full_moltbook_scan():
    """完整Moltbook扫描 - 热门帖子 + 用户主页"""
    print("="*70)
    print("🔥 Moltbook 完整深度扫描任务")
    print("="*70)
    print()
    
    extractor = MoltbookSuperExtractor()
    results = {}
    
    # 1. 扫描热门帖子
    print("【1/3】扫描热门帖子 (sort_by=hot)...")
    try:
        hot_posts = await extractor.run(mode="hot")
        results['hot_posts'] = hot_posts
        print(f"✅ 热门帖子: {len(hot_posts)} 条")
    except Exception as e:
        print(f"❌ 热门帖子扫描失败: {e}")
        results['hot_posts'] = []
    
    print()
    
    # 2. 扫描最新帖子
    print("【2/3】扫描最新帖子 (sort_by=new)...")
    try:
        # 使用extract_feed直接获取new
        new_posts = await extractor.extract_feed(sort_by="new")
        results['new_posts'] = new_posts
        print(f"✅ 最新帖子: {len(new_posts)} 条")
    except Exception as e:
        print(f"❌ 最新帖子扫描失败: {e}")
        results['new_posts'] = []
    
    print()
    
    # 3. 扫描用户主页 (LinLin_v1)
    print(f"【3/3】扫描用户主页 ({CONFIG['username']})...")
    try:
        profile_posts = await extractor.run(mode="profile", username=CONFIG['username'])
        results['profile_posts'] = profile_posts
        print(f"✅ 用户主页: {len(profile_posts)} 条")
    except Exception as e:
        print(f"❌ 用户主页扫描失败: {e}")
        results['profile_posts'] = []
    
    print()
    print("="*70)
    print("📊 扫描完成")
    print("="*70)
    print(f"  热门帖子: {len(results['hot_posts'])} 条")
    print(f"  最新帖子: {len(results['new_posts'])} 条")
    print(f"  用户主页: {len(results['profile_posts'])} 条")
    print(f"  总计: {sum(len(v) for v in results.values())} 条")
    print("="*70)
    
    return results

if __name__ == "__main__":
    asyncio.run(full_moltbook_scan())
