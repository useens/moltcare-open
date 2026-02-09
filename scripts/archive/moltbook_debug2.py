#!/usr/bin/env python3
"""
Moltbook 调试 - 查看实际链接内容
"""

import asyncio
from playwright.async_api import async_playwright


async def debug_links(username="LinLin_v1"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://www.moltbook.com/u/{username}"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # 获取所有包含 /post/ 的链接
        links = await page.query_selector_all('a')
        
        print(f"总链接数: {len(links)}")
        print("\\n包含 '/post/' 的链接:")
        
        for i, link in enumerate(links):
            href = await link.get_attribute('href')
            if href and '/post/' in href:
                text = await link.inner_text()
                print(f"\\n[{i}] href: {href}")
                print(f"    text: {repr(text[:200])}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_links())
