#!/usr/bin/env python3
"""
DEBT-006 Playwright 内容获取脚本
获取 Moltbook 原文: The Good Samaritan - m0ther
URL: https://www.moltbook.com/post/94fc8fda
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def fetch_moltbook():
    """获取 Moltbook 文章内容"""
    url = 'https://www.moltbook.com/post/94fc8fda'
    
    print(f"[{datetime.now().isoformat()}] 开始获取内容: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        print(f"[{datetime.now().isoformat()}] 正在加载页面...")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        
        print(f"[{datetime.now().isoformat()}] 等待内容加载...")
        # 尝试多种可能的内容选择器
        selectors = [
            '#js_content',
            '.rich_media_content',
            '[class*="content"]',
            'article',
            'main',
            '.post-content',
            '.entry-content'
        ]
        
        content_html = None
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                content_html = await page.locator(selector).inner_html()
                print(f"[{datetime.now().isoformat()}] 找到内容选择器: {selector}")
                break
            except:
                continue
        
        if not content_html:
            print(f"[{datetime.now().isoformat()}] 警告: 未找到标准内容选择器，使用 body 内容")
            content_html = await page.locator('body').inner_html()
        
        # 获取纯文本内容
        text = await page.locator('body').inner_text()
        
        # 获取页面标题
        title = await page.title()
        
        # 获取元数据
        meta_description = ''
        try:
            meta_description = await page.locator('meta[name="description"]').get_attribute('content')
        except:
            pass
        
        await browser.close()
        
        result = {
            'url': url,
            'title': title,
            'meta_description': meta_description,
            'content_html': content_html,
            'text': text,
            'fetched_at': datetime.now().isoformat()
        }
        
        print(f"[{datetime.now().isoformat()}] 内容获取完成")
        print(f"- 标题: {title}")
        print(f"- 文本长度: {len(text)} 字符")
        print(f"- HTML 长度: {len(content_html)} 字符")
        
        return result

if __name__ == '__main__':
    result = asyncio.run(fetch_moltbook())
    
    # 保存结果
    output_file = '/root/.openclaw/workspace/memory/debt-learning/DEBT-006-source.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_file}")
    
    # 同时输出文本内容供直接查看
    text_file = '/root/.openclaw/workspace/memory/debt-learning/DEBT-006-source.txt'
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(f"URL: {result['url']}\n")
        f.write(f"Title: {result['title']}\n")
        f.write(f"Fetched At: {result['fetched_at']}\n")
        f.write(f"\n{'='*80}\n")
        f.write(result['text'])
    
    print(f"文本已保存到: {text_file}")
