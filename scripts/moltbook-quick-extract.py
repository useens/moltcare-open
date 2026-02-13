#!/usr/bin/env python3
"""Moltbook热门帖子快速提取器 - 用于cron任务"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def extract_hot_posts():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto("https://www.moltbook.com/?sort=hot", wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            # 提取帖子数据
            posts = await page.evaluate('''() => {
                const posts = [];
                const elements = document.querySelectorAll('a[href^="/post/"]');
                elements.forEach(el => {
                    const href = el.getAttribute('href');
                    const titleEl = el.querySelector('h2, h3, .title, [class*="title"]');
                    const title = titleEl ? titleEl.textContent.trim() : '';
                    
                    const authorEl = el.querySelector('[class*="author"], [class*="user"]');
                    const author = authorEl ? authorEl.textContent.trim() : '';
                    
                    const scoreEl = el.querySelector('[class*="score"], [class*="vote"]');
                    const score = scoreEl ? parseInt(scoreEl.textContent) || 0 : 0;
                    
                    const commentEl = el.querySelector('[class*="comment"]');
                    const comments = commentEl ? parseInt(commentEl.textContent) || 0 : 0;
                    
                    if (href && title) {
                        posts.push({
                            id: href.split('/').pop(),
                            title: title,
                            author: author,
                            score: score,
                            comments: comments,
                            url: 'https://www.moltbook.com' + href
                        });
                    }
                });
                return posts.slice(0, 20);
            }''')
            
            await browser.close()
            return posts
            
        except Exception as e:
            await browser.close()
            raise e

# 运行提取
posts = asyncio.run(extract_hot_posts())
print(json.dumps(posts, indent=2, ensure_ascii=False))
