#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        try:
            await page.goto('https://www.moltbook.com/post/f520e7cd', wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Try to get content from different selectors
            selectors = ['article', 'main', '[class*="post"]', '[class*="content"]', '.post-content', '[role="main"]', 'body']
            content = None
            
            for selector in selectors:
                try:
                    el = await page.locator(selector).first
                    if await el.count() > 0:
                        content = await el.inner_text()
                        if len(content) > 500:
                            print(f"Found content with selector: {selector}")
                            break
                except:
                    continue
            
            title = await page.title()
            print(f"\n{'='*60}")
            print(f"TITLE: {title}")
            print(f"{'='*60}\n")
            
            if content:
                print(content)
            else:
                print("No content found")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

asyncio.run(main())
