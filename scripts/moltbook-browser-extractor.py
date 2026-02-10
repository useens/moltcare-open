#!/usr/bin/env python3
"""
Moltbook 提取器 v4.1 - 完整版
成功提取用户主页帖子数据（含点赞/评论）
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright


async def extract_moltbook(username="LinLin_v1"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://www.moltbook.com/u/{username}"
        print(f"[INFO] 访问: {url}")
        
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        links = await page.query_selector_all('a')
        
        posts = []
        seen_ids = {}
        
        for link in links:
            href = await link.get_attribute('href')
            if not href or '/post/' not in href:
                continue
                
            post_id = href.replace('/post/', '')
            text = await link.inner_text()
            
            # 提取点赞/评论/时间
            upvote_match = re.search(r'▲\s*(\d+)', text)
            likes = int(upvote_match.group(1)) if upvote_match else 0
            
            comment_match = re.search(r'💬\s*(\d+)', text)
            comments = int(comment_match.group(1)) if comment_match else 0
            
            time_match = re.search(r'•\s*([\d/]+,\s*[\d:]+\s*[AP]M)', text)
            time_str = time_match.group(1) if time_match else None
            
            # 分割行找标题
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            title = None
            for line in lines:
                if 'm/showcase' not in line and '▲' not in line and '💬' not in line:
                    if len(line) > 10:
                        title = line[:200]
                        break
            
            # 合并同一post的数据
            if post_id in seen_ids:
                existing = seen_ids[post_id]
                if likes > existing['likes']:
                    existing['likes'] = likes
                if comments > existing['comments']:
                    existing['comments'] = comments
                if title and not existing.get('title'):
                    existing['title'] = title
                if time_str and not existing.get('publish_time'):
                    existing['publish_time'] = time_str
            elif title:
                post_data = {
                    "post_id": post_id,
                    "title": title,
                    "submolt": "m/showcase",
                    "publish_time": time_str,
                    "likes": likes,
                    "comments": comments,
                    "url": f"https://www.moltbook.com{href}"
                }
                seen_ids[post_id] = post_data
                posts.append(post_data)
        
        # 截图
        screenshot = f"moltbook_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=screenshot, full_page=True)
        
        await browser.close()
        
        result = {
            "username": username,
            "extraction_time": datetime.now().isoformat(),
            "total_posts": len(posts),
            "posts": posts,
            "screenshot": screenshot
        }
        
        with open("moltbook_data.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result


if __name__ == "__main__":
    result = asyncio.run(extract_moltbook())
    
    print(f"\n=== 提取完成 ===")
    print(f"用户: {result['username']}")
    print(f"帖子数: {result['total_posts']}")
    
    for i, p in enumerate(result['posts'], 1):
        print(f"\n[{i}] {p['title'][:70]}...")
        print(f"    👍 {p['likes']} | 💬 {p['comments']} | 🕐 {p['publish_time']}")
        print(f"    🔗 {p['url']}")
    
    print(f"\n截图: {result['screenshot']}")
    print(f"数据: moltbook_data.json")
