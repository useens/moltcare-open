#!/usr/bin/env python3
"""
尝试多种方法获取Moltbook帖子内容
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def try_fetch():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        
        # 尝试1: 标准桌面UA
        context1 = await browser.new_context(
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page1 = await context1.new_page()
        
        print("=== Attempt 1: Standard Desktop ===")
        await page1.goto('https://www.moltbook.com/post/f520e7cd', wait_until='networkidle', timeout=60000)
        await page1.wait_for_timeout(5000)
        
        content1 = await page1.content()
        print(f"HTML length: {len(content1)}")
        
        # Check for specific content
        if "Post not found" in content1:
            print("Result: Post not found (404)")
        elif "login" in content1.lower() or "Login" in content1:
            print("Result: Requires login")
        else:
            # Try to extract content
            body_text = await page1.locator('body').inner_text()
            print(f"Body text length: {len(body_text)}")
            print(f"Body preview: {body_text[:500]}")
        
        await context1.close()
        
        # 尝试2: 移动端UA
        context2 = await browser.new_context(
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            viewport={'width': 390, 'height': 844}
        )
        page2 = await context2.new_page()
        
        print("\n=== Attempt 2: Mobile UA ===")
        await page2.goto('https://www.moltbook.com/post/f520e7cd', wait_until='networkidle', timeout=60000)
        await page2.wait_for_timeout(5000)
        
        content2 = await page2.content()
        body_text2 = await page2.locator('body').inner_text()
        print(f"Body text length: {len(body_text2)}")
        
        if "Silicon" in body_text2 or "Zoo" in body_text2 or "diversity" in body_text2.lower():
            print("✓ Found relevant content!")
            print(body_text2[:3000])
        else:
            print("Result: No relevant content found")
            print(f"Preview: {body_text2[:500]}")
        
        await context2.close()
        await browser.close()

asyncio.run(try_fetch())
