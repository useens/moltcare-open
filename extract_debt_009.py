#!/usr/bin/env python3
"""提取DEBT-009内容"""
import asyncio
from playwright.async_api import async_playwright

async def extract_post():
    url = "https://www.moltbook.com/post/6fe6491e"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        print(f"🔍 提取: {url}")
        
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(5000)  # 等待JS渲染
        
        # 提取标题
        title = await page.title()
        print(f"标题: {title}")
        
        # 提取完整内容 - 尝试多种选择器
        content = ""
        selectors = ['article', 'main', '[class*="post"]', '[class*="content"]', 'body']
        
        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    content = await elem.inner_text()
                    if len(content) > 500:
                        print(f"✅ 使用选择器 '{selector}' 提取到 {len(content)} 字符")
                        break
            except Exception as e:
                continue
        
        # 提取评论
        comments = []
        comment_selectors = ['[class*="comment"]', '.reply', '[data-testid*="comment"]']
        for sel in comment_selectors:
            try:
                elems = await page.query_selector_all(sel)
                for elem in elems[:15]:
                    text = await elem.inner_text()
                    if len(text) > 20:
                        comments.append(text[:500])
                if comments:
                    break
            except:
                pass
        
        await browser.close()
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "comments": comments
        }

# 执行提取
result = asyncio.run(extract_post())

# 输出结果
import json
print("\n" + "="*60)
print(json.dumps(result, ensure_ascii=False, indent=2)[:8000])
