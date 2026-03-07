#!/usr/bin/env python3
"""
DEBT-005: Moltbook 内容获取脚本 (简化版)
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def fetch_moltbook():
    print("[INFO] 启动 Playwright...")
    
    async with async_playwright() as p:
        print("[INFO] 启动 Chromium...")
        browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        url = 'https://www.moltbook.com/post/2fdd8e55'
        
        print(f"[INFO] 访问: {url}")
        
        # 访问页面
        response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        print(f"[INFO] 页面响应状态: {response.status}")
        
        # 等待网络空闲和 JavaScript 执行
        print("[INFO] 等待页面渲染...")
        await page.wait_for_load_state('networkidle', timeout=30000)
        await asyncio.sleep(3)  # 额外等待确保动态内容加载
        
        # 获取页面内容
        title = await page.title()
        print(f"[INFO] 标题: {title}")
        
        # 获取完整 HTML
        html = await page.content()
        
        # 获取纯文本
        text = await page.locator('body').inner_text()
        
        # 尝试获取文章内容
        article_text = ""
        selectors = ['article', 'main', '[class*="post"]', '[class*="content"]', '.prose']
        
        for sel in selectors:
            try:
                elem = await page.query_selector(sel)
                if elem:
                    txt = await elem.inner_text()
                    if len(txt) > 500:
                        article_text = txt
                        print(f"[INFO] 找到内容区域: {sel} ({len(txt)} 字符)")
                        break
            except:
                pass
        
        if not article_text:
            article_text = text
            print(f"[INFO] 使用 body 文本: {len(text)} 字符")
        
        await browser.close()
        
        result = {
            'url': url,
            'title': title,
            'timestamp': datetime.now().isoformat(),
            'text_length': len(text),
            'article_text': article_text[:50000]  # 限制大小
        }
        
        return result

if __name__ == '__main__':
    try:
        result = asyncio.run(fetch_moltbook())
        
        # 保存结果
        with open('/root/.openclaw/workspace/memory/debt-learning/DEBT-005-content.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        with open('/root/.openclaw/workspace/memory/debt-learning/DEBT-005-content.txt', 'w', encoding='utf-8') as f:
            f.write(f"标题: {result['title']}\n")
            f.write(f"URL: {result['url']}\n")
            f.write(f"获取时间: {result['timestamp']}\n")
            f.write("=" * 80 + "\n\n")
            f.write(result['article_text'])
        
        print("\n[SUCCESS] 内容已保存!")
        print(f"- JSON: DEBT-005-content.json")
        print(f"- TXT: DEBT-005-content.txt")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
