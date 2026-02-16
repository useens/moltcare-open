import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def fetch_moltbook():
    """Fetch Moltbook article content using Playwright"""
    print(f"[{datetime.now()}] Starting to fetch Moltbook article...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800},
            locale='zh-CN'
        )
        
        page = await context.new_page()
        
        # Enable request/response logging for debugging
        page.on("console", lambda msg: print(f"[Console] {msg.text}") if msg.type == "error" else None)
        
        try:
            print(f"[{datetime.now()}] Navigating to URL...")
            await page.goto('https://www.moltbook.com/post/562faad7', wait_until='networkidle', timeout=60000)
            
            print(f"[{datetime.now()}] Waiting for content to load...")
            # Try multiple possible selectors
            selectors = [
                '#js_content',
                '.rich_media_content', 
                'article',
                '[class*="content"]',
                'main',
                '.post-content',
                '.article-content'
            ]
            
            content = None
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    print(f"[{datetime.now()}] Found selector: {selector}")
                    content = await page.locator(selector).inner_text()
                    if content and len(content.strip()) > 100:
                        break
                except:
                    continue
            
            # Get page title
            title = await page.title()
            print(f"[{datetime.now()}] Page title: {title}")
            
            # Get full text as fallback
            if not content or len(content.strip()) < 100:
                print(f"[{datetime.now()}] Using body text as fallback...")
                content = await page.locator('body').inner_text()
            
            # Get HTML content for structure analysis
            html_content = await page.content()
            
            await browser.close()
            
            result = {
                'title': title,
                'url': 'https://www.moltbook.com/post/562faad7',
                'content': content,
                'html_length': len(html_content),
                'content_length': len(content) if content else 0,
                'fetched_at': datetime.now().isoformat()
            }
            
            print(f"[{datetime.now()}] Fetch completed. Content length: {len(content) if content else 0} chars")
            return result
            
        except Exception as e:
            await browser.close()
            print(f"[{datetime.now()}] Error: {str(e)}")
            raise

if __name__ == '__main__':
    result = asyncio.run(fetch_moltbook())
    
    # Save to file
    output_file = '/root/.openclaw/workspace/moltbook_raw_content.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Title: {result['title']}")
    print(f"Content length: {result['content_length']} characters")
    print(f"Saved to: {output_file}")
    print(f"{'='*60}\n")
    
    # Print preview
    if result['content']:
        preview = result['content'][:2000] if len(result['content']) > 2000 else result['content']
        print("Content Preview:")
        print("-" * 60)
        print(preview)
        print("-" * 60)
