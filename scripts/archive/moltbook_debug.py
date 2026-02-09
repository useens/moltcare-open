#!/usr/bin/env python3
"""
Moltbook 数据提取器 v3.0 - 调试版
获取页面HTML结构以分析选择器
"""

import asyncio
from playwright.async_api import async_playwright


async def debug_page_structure(username="LinLin_v1"):
    """调试页面结构"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://www.moltbook.com/u/{username}"
        print(f"访问: {url}")
        
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # 获取页面HTML前5000字符
        html = await page.content()
        print(f"\\n页面HTML长度: {len(html)} 字符")
        print(f"\\n前3000字符预览:")
        print(html[:3000])
        
        # 查找包含"Digital Immortality"的元素
        elements = await page.query_selector_all('*')
        print(f"\\n页面总元素数: {len(elements)}")
        
        # 查找所有链接
        links = await page.query_selector_all('a')
        print(f"链接数量: {len(links)}")
        
        for i, link in enumerate(links[:10]):
            text = await link.inner_text()
            href = await link.get_attribute('href')
            if text and len(text) > 10:
                print(f"  [{i}] {text[:80]}... -> {href}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_page_structure())
