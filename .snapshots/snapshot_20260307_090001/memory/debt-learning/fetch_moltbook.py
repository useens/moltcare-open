#!/usr/bin/env python3
"""
Playwright 脚本 - 获取 Moltbook 文章原文
目标: https://www.moltbook.com/post/4b64728c
"""

import asyncio
from playwright.async_api import async_playwright

async def fetch_moltbook():
    """使用 Playwright 获取 Moltbook 文章全文"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        print("🌐 正在访问页面...")
        await page.goto('https://www.moltbook.com/post/4b64728c', 
                       wait_until='networkidle', timeout=30000)
        
        print("⏳ 等待内容加载...")
        await page.wait_for_timeout(3000)
        
        # 尝试多种选择器来定位文章内容
        selectors = [
            '#js_content',
            '.rich_media_content',
            '[class*="content"]',
            '[class*="post"]',
            'article',
            'main',
            '.article-content',
            '.post-content'
        ]
        
        content_html = None
        content_text = None
        
        for selector in selectors:
            try:
                print(f"  尝试选择器: {selector}")
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    content_html = await element.inner_html()
                    content_text = await element.inner_text()
                    print(f"  ✓ 找到内容: {selector}")
                    break
            except Exception as e:
                print(f"  ✗ {selector} 失败: {str(e)[:50]}")
                continue
        
        # 如果没找到，获取整个 body
        if not content_text:
            print("⚠️ 未找到特定内容区域，获取整个页面...")
            content_html = await page.content()
            content_text = await page.locator('body').inner_text()
        
        # 获取页面标题
        try:
            title = await page.title()
        except:
            title = "无标题"
        
        await browser.close()
        
        return {
            'title': title,
            'html': content_html,
            'text': content_text
        }

async def save_content():
    """保存获取的内容到文件"""
    result = await fetch_moltbook()
    
    print(f"\n📄 标题: {result['title']}")
    print(f"📝 内容长度: {len(result['text'])} 字符")
    
    # 保存文本内容
    with open('/root/.openclaw/workspace/memory/debt-learning/DEBT-004-source.txt', 'w', encoding='utf-8') as f:
        f.write(f"=== {result['title']} ===\n")
        f.write(f"=== URL: https://www.moltbook.com/post/4b64728c ===\n")
        f.write(f"=== 获取时间: 2026-02-16 ===\n\n")
        f.write(result['text'])
    
    # 保存 HTML 内容
    with open('/root/.openclaw/workspace/memory/debt-learning/DEBT-004-source.html', 'w', encoding='utf-8') as f:
        f.write(result['html'])
    
    print("✅ 内容已保存到 DEBT-004-source.txt 和 .html")
    return result

if __name__ == '__main__':
    result = asyncio.run(save_content())
    print(f"\n🔍 内容预览 (前500字符):")
    print(result['text'][:500])
