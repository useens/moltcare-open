#!/usr/bin/env python3
"""
分析Moltbook当前页面结构
"""

import asyncio
from playwright.async_api import async_playwright

async def analyze_moltbook():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path="/usr/bin/chromium"
        )
        page = await browser.new_page()
        
        print("🔍 分析Moltbook页面结构...")
        print("="*70)
        
        await page.goto("https://www.moltbook.com/?sort=hot", timeout=30000)
        await page.wait_for_load_state("networkidle")
        
        # 获取页面HTML结构
        html = await page.content()
        
        # 检查各种可能的选择器
        selectors_to_check = [
            'a[href^="/post/"]',
            'a[href*="/post/"]',
            'article',
            '[class*="post"]',
            '[class*="thread"]',
            '.post',
            '.thread',
            'main a',
            '[role="article"]',
            'div[class*="content"]',
            'div > a'
        ]
        
        print("\n【检查各种选择器】")
        for selector in selectors_to_check:
            try:
                elements = await page.query_selector_all(selector)
                print(f"  {selector}: {len(elements)} 个元素")
                if len(elements) > 0 and len(elements) < 20:
                    # 显示前3个元素的href或text
                    for i, el in enumerate(elements[:3]):
                        href = await el.get_attribute('href') or 'N/A'
                        text = await el.inner_text()
                        text = text[:50] if text else 'N/A'
                        print(f"    [{i+1}] href={href}, text={text[:40]}...")
            except Exception as e:
                print(f"  {selector}: 错误 - {e}")
        
        # 获取页面中所有的链接
        print("\n【页面中所有链接 (前20个)】")
        links = await page.query_selector_all('a')
        link_count = 0
        for link in links[:20]:
            href = await link.get_attribute('href')
            if href and href.startswith('/'):
                text = await link.inner_text()
                text = text[:40] if text else 'N/A'
                print(f"  {href}: {text}")
                link_count += 1
        
        print(f"\n总共找到 {link_count} 个内部链接")
        print("="*70)
        
        await browser.close()

asyncio.run(analyze_moltbook())
