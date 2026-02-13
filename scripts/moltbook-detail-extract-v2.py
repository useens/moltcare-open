#!/usr/bin/env python3
"""Moltbook详情页深度提取器 - 增强版"""

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
            
            # 等待页面加载 - 增加等待时间
            await page.wait_for_timeout(5000)
            
            # 等待内容出现
            try:
                await page.wait_for_selector('h1', timeout=10000)
            except:
                pass
            
            # 提取完整内容
            data = await page.evaluate('''() => {
                // 标题
                const titleEl = document.querySelector('h1');
                const title = titleEl ? titleEl.textContent.trim() : '';
                
                // 作者
                const authorLinks = document.querySelectorAll('a[href^="/u/"]');
                const author = authorLinks.length > 0 ? authorLinks[0].textContent.trim() : '';
                
                // 正文 - 尝试多种选择器
                let content = '';
                const contentSelectors = ['article', '[class*="prose"]', '[class*="content"]', 'main > div', '.post-content'];
                for (const sel of contentSelectors) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText.trim().length > content.length) {
                        content = el.innerText.trim();
                    }
                }
                
                // 如果还没找到，尝试获取main内的所有文本
                if (!content) {
                    const main = document.querySelector('main');
                    if (main) {
                        content = main.innerText.trim().substring(0, 2000);
                    }
                }
                
                // 分数
                const scoreMatch = document.body.innerText.match(/(\d+)\s*points?/);
                const score = scoreMatch ? scoreMatch[1] : '0';
                
                // 评论
                const comments = [];
                const commentEls = document.querySelectorAll('[class*="comment"], article div div');
                commentEls.forEach(el => {
                    const text = el.textContent.trim();
                    if (text.length > 20 && text.length < 500) {
                        comments.push(text.substring(0, 200));
                    }
                });
                
                // 完整HTML用于调试
                const bodyText = document.body.innerText.substring(0, 1500);
                
                return { title, author, content, score, comments: comments.slice(0, 5), bodyPreview: bodyText };
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
