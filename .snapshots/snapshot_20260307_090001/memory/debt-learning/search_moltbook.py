#!/usr/bin/env python3
"""
Playwright 脚本 - 搜索 Moltbook 相关内容
目标: 搜索 Quiet Power of Operator 或 Jackle
"""

import asyncio
from playwright.async_api import async_playwright

async def search_moltbook():
    """搜索 Moltbook 相关内容"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        print("🌐 访问 Moltbook 首页...")
        await page.goto('https://www.moltbook.com/', wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(3000)
        
        # 获取页面文本
        text = await page.locator('body').inner_text()
        title = await page.title()
        
        # 保存首页内容
        with open('/root/.openclaw/workspace/memory/debt-learning/moltbook_homepage.txt', 'w', encoding='utf-8') as f:
            f.write(f"=== {title} ===\n\n")
            f.write(text)
        
        print(f"✅ 首页已保存，长度: {len(text)} 字符")
        print(f"\n🔍 首页内容预览 (前1500字符):")
        print("=" * 60)
        print(text[:1500])
        print("=" * 60)
        
        # 尝试搜索功能
        print("\n🔎 尝试搜索 'Jackle'...")
        try:
            # 尝试找到搜索框
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="search" i]',
                'input[name="q"]',
                '[class*="search"] input'
            ]
            
            for selector in search_selectors:
                try:
                    search_box = await page.wait_for_selector(selector, timeout=2000)
                    if search_box:
                        await search_box.fill('Jackle')
                        await search_box.press('Enter')
                        await page.wait_for_timeout(3000)
                        
                        results_text = await page.locator('body').inner_text()
                        with open('/root/.openclaw/workspace/memory/debt-learning/moltbook_search_jackle.txt', 'w', encoding='utf-8') as f:
                            f.write(results_text)
                        
                        print(f"✅ 搜索结果已保存")
                        break
                except:
                    continue
        except Exception as e:
            print(f"⚠️ 搜索失败: {e}")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(search_moltbook())
