#!/usr/bin/env python3
"""Moltbook详情页深度提取器"""

import asyncio
import json
import sys
from playwright.async_api import async_playwright

async def extract_post_detail(post_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            url = f"https://www.moltbook.com/post/{post_id}"
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            # 提取完整内容
            data = await page.evaluate('''() => {
                // 标题
                const titleEl = document.querySelector('h1, [class*="title"]');
                const title = titleEl ? titleEl.textContent.trim() : '';
                
                // 作者
                const authorEl = document.querySelector('[class*="author"], a[href^="/u/"]');
                const author = authorEl ? authorEl.textContent.trim() : '';
                
                // 正文内容
                const contentEl = document.querySelector('article, [class*="content"], [class*="body"]');
                const content = contentEl ? contentEl.innerText.trim() : '';
                
                // 分数和评论数
                const scoreEl = document.querySelector('[class*="score"]');
                const score = scoreEl ? scoreEl.textContent.trim() : '0';
                
                // 评论
                const comments = [];
                const commentEls = document.querySelectorAll('[class*="comment"]');
                commentEls.forEach(el => {
                    const author = el.querySelector('[class*="author"]');
                    const text = el.querySelector('[class*="text"], [class*="content"]');
                    if (text) {
                        comments.push({
                            author: author ? author.textContent.trim() : 'Unknown',
                            text: text.textContent.trim()
                        });
                    }
                });
                
                return { title, author, content, score, comments };
            }''')
            
            await browser.close()
            return data
            
        except Exception as e:
            await browser.close()
            return {"error": str(e)}

# 主函数
if __name__ == "__main__":
    post_ids = sys.argv[1:] if len(sys.argv) > 1 else []
    
    results = {}
    for pid in post_ids:
        print(f"Extracting {pid}...", file=sys.stderr)
        results[pid] = asyncio.run(extract_post_detail(pid))
    
    print(json.dumps(results, indent=2, ensure_ascii=False))
