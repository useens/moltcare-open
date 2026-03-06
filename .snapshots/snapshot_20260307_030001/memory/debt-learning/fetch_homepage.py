#!/usr/bin/env python3
"""
获取 Moltbook 主页帖子列表
"""

import asyncio
from playwright.async_api import async_playwright

async def fetch_homepage():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        print("[INFO] 访问 Moltbook 主页...")
        await page.goto('https://www.moltbook.com/', wait_until='networkidle', timeout=60000)
        await asyncio.sleep(3)
        
        # 获取所有包含 post 的链接
        links = await page.query_selector_all('a[href*="/post/"]')
        
        posts = []
        for link in links[:20]:  # 只取前20个
            try:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                if href and '/post/' in href:
                    posts.append({'href': href, 'text': text[:100]})
            except:
                pass
        
        print(f"\n[INFO] 找到 {len(posts)} 个帖子链接:\n")
        for p in posts[:10]:
            print(f"  - {p['href']}: {p['text'][:50]}...")
        
        # 搜索 Fred 的帖子
        fred_posts = [p for p in posts if 'fred' in p['text'].lower() or 'podcast' in p['text'].lower()]
        print(f"\n[INFO] Fred/Podcast 相关帖子: {len(fred_posts)}")
        for p in fred_posts:
            print(f"  -> {p['href']}: {p['text'][:80]}")
        
        await browser.close()
        return posts

if __name__ == '__main__':
    asyncio.run(fetch_homepage())
