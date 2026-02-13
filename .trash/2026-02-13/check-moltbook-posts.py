#!/usr/bin/env python3
"""
检查Moltbook首页帖子列表位置
"""

import asyncio
from playwright.async_api import async_playwright

async def find_posts():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path="/usr/bin/chromium"
        )
        page = await browser.new_page()
        
        print("🔍 检查Moltbook首页帖子...")
        print("="*70)
        
        await page.goto("https://www.moltbook.com/?sort=hot", timeout=30000)
        await page.wait_for_load_state("networkidle")
        
        # 等待一段时间让JS渲染
        await asyncio.sleep(3)
        
        # 再次检查选择器
        print("\n【3秒后检查】")
        selectors = [
            'a[href^="/post/"]',
            'a[href*="/post/"]',
            'article a',
            '[class*="post"] a',
            'main a',
            'body a'
        ]
        
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            print(f"  {selector}: {len(elements)} 个")
            if len(elements) > 0:
                print(f"    示例:")
                for i, el in enumerate(elements[:3]):
                    href = await el.get_attribute('href') or 'N/A'
                    text = await el.inner_text()
                    text = text[:40] if text else 'N/A'
                    print(f"      [{i+1}] {href}: {text}")
        
        # 获取完整的HTML看结构
        print("\n【页面标题】")
        title = await page.title()
        print(f"  {title}")
        
        # 检查是否有加载指示器
        print("\n【检查加载状态】")
        body_text = await page.inner_text('body')
        if 'the front page of the agent internet' in body_text:
            print("  ✅ 页面标语正确")
        if 'Login' in body_text:
            print("  ⚠️  页面有登录按钮")
        if '🦞' in body_text:
            print("  ✅ 页面有螃蟹图标")
        
        await browser.close()

asyncio.run(find_posts())
