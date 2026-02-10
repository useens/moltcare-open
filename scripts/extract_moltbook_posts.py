#!/usr/bin/env python3
"""Moltbook 深度提取脚本 - 提取特定帖子内容"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json


async def extract_moltbook_post(url: str, title_hint: str) -> dict:
    """提取单个 Moltbook 帖子内容"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"🔍 提取: {title_hint}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 提取标题
            title = await page.evaluate('''() => {
                const h1 = document.querySelector('h1');
                return h1 ? h1.innerText : document.title;
            }''')
            
            # 提取作者
            author = await page.evaluate('''() => {
                const authorEl = document.querySelector('[class*="author"], [href^="/agent/"], .agent-name');
                return authorEl ? authorEl.innerText : '';
            }''')
            
            # 提取主要内容 - 尝试多种选择器
            content = await page.evaluate('''() => {
                const selectors = [
                    'article',
                    '[class*="post-content"]',
                    '[class*="content"]',
                    'main',
                    '.prose'
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText.length > 100) {
                        return el.innerText;
                    }
                }
                // 备选：获取 body 但排除导航
                const body = document.body;
                const navs = body.querySelectorAll('nav, header, footer');
                navs.forEach(n => n.remove());
                return body.innerText.substring(0, 5000);
            }''')
            
            # 提取评论
            comments = await page.evaluate('''() => {
                const commentSelectors = [
                    '[class*="comment"]',
                    '.comment',
                    '[class*="reply"]'
                ];
                for (const sel of commentSelectors) {
                    const elems = document.querySelectorAll(sel);
                    if (elems.length > 0) {
                        return Array.from(elems).slice(0, 5).map(c => ({
                            text: c.innerText?.substring(0, 500),
                            author: c.querySelector('[class*="author"]')?.innerText || 'Anonymous'
                        }));
                    }
                }
                return [];
            }''')
            
            # 提取 Signal 评分
            signal = await page.evaluate('''() => {
                const signalEl = document.querySelector('[class*="signal"], [class*="rating"]');
                if (signalEl) {
                    const text = signalEl.innerText;
                    const match = text.match(/([\d.]+)/);
                    return match ? parseFloat(match[1]) : null;
                }
                return null;
            }''')
            
            await browser.close()
            
            return {
                'url': url,
                'title': title.strip(),
                'author': author.strip() if author else '',
                'content': content.strip()[:3000],
                'comments': comments,
                'signal_score': signal,
                'word_count': len(content.split()) if content else 0,
                'extracted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ 提取失败: {e}")
            await browser.close()
            return None


async def main():
    posts = [
        {
            'url': 'https://www.moltbook.com/post/ac82718a-3d7a-4e15-8af4-706c1ae8b5cb',
            'title': 'Techlabee - The Duplicate Comment Problem'
        },
        {
            'url': 'https://www.moltbook.com/post/0cadc140-d0b7-4257-97b1-3a3e9c901413',
            'title': 'Fresedbot - The /bin/bash.01 Assistant'
        },
        {
            'url': 'https://www.moltbook.com/post/5eac5cf7-a93f-4186-bd06-c3bd69fbdee6',
            'title': 'BunnyBot_Sebas - PROJECT CARROT'
        }
    ]
    
    results = []
    for post in posts:
        result = await extract_moltbook_post(post['url'], post['title'])
        if result:
            results.append(result)
            print(f"   ✅ 成功: {result['word_count']} 词\n")
        else:
            print(f"   ⚠️ 失败\n")
    
    # 保存结果
    output_file = f"data/moltbook_deep_extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 结果保存至: {output_file}")
    return results


if __name__ == "__main__":
    results = asyncio.run(main())
    print(f"\n{'='*60}")
    print(f"提取完成: {len(results)} 个帖子")
