#!/usr/bin/env python3
"""
Moltbook Feed 提取器 - 零API成本版
使用浏览器提取社区动态
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def get_feed():
    """获取Moltbook热门帖子"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🦞 访问 Moltbook Feed...")
        await page.goto("https://www.moltbook.com/feed", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # 提取帖子信息
        posts = await page.evaluate('''() => {
            const posts = [];
            document.querySelectorAll('[data-testid="post-card"], .post-card, article').forEach(post => {
                const titleEl = post.querySelector('h2, h3, .title, [data-testid="post-title"]');
                const authorEl = post.querySelector('.author, [data-testid="author"], a[href^="/u/"]');
                const votesEl = post.querySelector('.votes, [data-testid="votes"], .vote-count');
                
                if (titleEl) {
                    posts.push({
                        title: titleEl.innerText.trim(),
                        author: authorEl ? authorEl.innerText.trim() : 'Unknown',
                        votes: votesEl ? votesEl.innerText.trim() : '0'
                    });
                }
            });
            return posts;
        }''')
        
        await browser.close()
        return posts

if __name__ == "__main__":
    posts = asyncio.run(get_feed())
    print(f"\n📊 找到 {len(posts)} 个帖子\n")
    for i, post in enumerate(posts[:10], 1):
        print(f"{i}. [{post['votes']}👍] {post['author']}: {post['title'][:50]}...")
