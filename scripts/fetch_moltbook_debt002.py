import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def fetch_moltbook():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        print(f"[{datetime.now()}] 正在加载页面...")
        await page.goto('https://www.moltbook.com/post/cbd6474f', wait_until='networkidle', timeout=60000)
        
        # 等待内容加载
        print(f"[{datetime.now()}] 等待内容选择器...")
        await page.wait_for_selector('#js_content, .rich_media_content, .post-content, article', timeout=20000)
        
        # 获取页面标题
        title = await page.title()
        print(f"标题: {title}")
        
        # 获取主要内容 - 尝试多种选择器
        content_selectors = [
            '#js_content',
            '.rich_media_content',
            '.post-content',
            'article',
            '.content',
            '[class*="article"]',
            '[class*="post"]'
        ]
        
        content_html = None
        content_text = None
        
        for selector in content_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=5000):
                    content_html = await element.inner_html()
                    content_text = await element.inner_text()
                    print(f"找到内容选择器: {selector}")
                    break
            except Exception as e:
                continue
        
        # 如果都没找到，获取 body 内容
        if not content_text:
            print("使用 body 作为备选...")
            content_html = await page.locator('body').inner_html()
            content_text = await page.locator('body').inner_text()
        
        await browser.close()
        
        return {
            'title': title,
            'url': 'https://www.moltbook.com/post/cbd6474f',
            'timestamp': datetime.now().isoformat(),
            'content_html': content_html,
            'content_text': content_text
        }

if __name__ == '__main__':
    result = asyncio.run(fetch_moltbook())
    
    # 保存结果
    output_file = '/root/.openclaw/workspace/moltbook_cbd6474f_raw.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 内容已保存到: {output_file}")
    print(f"✓ 内容长度: {len(result['content_text'])} 字符")
    print("\n--- 内容预览 (前2000字符) ---")
    print(result['content_text'][:2000])
