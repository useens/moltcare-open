#!/usr/bin/env python3
"""获取Moltbook文章内容的备用方案"""
import asyncio
import sys
from playwright.async_api import async_playwright

async def fetch_article(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')
        
        # 等待内容加载
        await asyncio.sleep(3)
        
        # 获取页面文本内容
        content = await page.evaluate('''() => {
            // 尝试找到文章主要内容
            const article = document.querySelector('article');
            if (article) return article.innerText;
            
            // 备选：获取main区域
            const main = document.querySelector('main');
            if (main) return main.innerText;
            
            // 最后尝试获取body文本
            return document.body.innerText;
        }''')
        
        # 获取标题
        title = await page.title()
        
        await browser.close()
        return title, content

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.moltbook.com/post/4b64728c"
    title, content = asyncio.run(fetch_article(url))
    print(f"=== TITLE: {title} ===")
    print(f"=== CONTENT ===")
    print(content)
