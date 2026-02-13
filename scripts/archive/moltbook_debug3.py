#!/usr/bin/env python3
"""
Moltbook 提取器 - 带调试
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright


async def extract_with_debug(username="LinLin_v1"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://www.moltbook.com/u/{username}"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        links = await page.query_selector_all('a')
        
        posts = []
        seen_ids = set()
        
        for i, link in enumerate(links):
            href = await link.get_attribute('href')
            if not href or '/post/' not in href:
                continue
                
            post_id = href.replace('/post/', '')
            if post_id in seen_ids:
                continue
            seen_ids.add(post_id)
            
            text = await link.inner_text()
            print(f"\\n=== Link {i} ===")
            print(f"ID: {post_id}")
            print(f"Text preview: {text[:150]}...")
            
            # 解析
            lines = [l.strip() for l in text.split('\\n') if l.strip()]
            print(f"Lines: {lines}")
            
            # 找标题
            title = None
            for line in lines:
                if 'm/showcase' not in line and '▲' not in line and '💬' not in line:
                    if len(line) > 10:
                        title = line[:200]
                        break
            
            print(f"Found title: {title}")
            
            if title:
                upvote_match = re.search(r'▲\\s*(\\d+)', text)
                likes = int(upvote_match.group(1)) if upvote_match else 0
                
                comment_match = re.search(r'💬\\s*(\\d+)', text)
                comments = int(comment_match.group(1)) if comment_match else 0
                
                posts.append({
                    "post_id": post_id,
                    "title": title,
                    "likes": likes,
                    "comments": comments
                })
        
        await browser.close()
        print(f"\\n\\n总计: {len(posts)} 个帖子")
        return posts


if __name__ == "__main__":
    posts = asyncio.run(extract_with_debug())
    for p in posts:
        print(f"- {p['title'][:60]}... (👍 {p['likes']}, 💬 {p['comments']})")
