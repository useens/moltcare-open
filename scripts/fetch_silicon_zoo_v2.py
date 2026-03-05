#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Add cookies if needed
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()
        
        try:
            # Navigate with longer timeout
            print("Navigating to page...")
            await page.goto('https://www.moltbook.com/post/f520e7cd', wait_until='domcontentloaded', timeout=90000)
            
            # Wait for content to load
            await page.wait_for_timeout(8000)
            
            # Try multiple selectors
            selectors = [
                'article',
                'main',
                '[class*="post-content"]',
                '[class*="content"]',
                '[class*="post"]',
                '[role="main"]',
                '.prose',
                '.markdown',
                'body'
            ]
            
            content = None
            used_selector = None
            
            for selector in selectors:
                try:
                    elements = await page.locator(selector).all()
                    for el in elements:
                        text = await el.inner_text()
                        if len(text) > 1000:  # Look for substantial content
                            content = text
                            used_selector = selector
                            break
                    if content:
                        break
                except Exception as e:
                    continue
            
            title = await page.title()
            url = page.url
            
            print(f"\n{'='*70}")
            print(f"URL: {url}")
            print(f"TITLE: {title}")
            print(f"SELECTOR: {used_selector}")
            print(f"{'='*70}\n")
            
            if content:
                print(content[:15000])  # Print first 15000 chars
                if len(content) > 15000:
                    print("\n...[truncated]...")
            else:
                # Print page HTML structure for debugging
                html = await page.content()
                print("No content found. HTML length:", len(html))
                # Try to find any text content
                body_text = await page.locator('body').inner_text()
                print("\nBody text preview:")
                print(body_text[:3000])
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

asyncio.run(main())
