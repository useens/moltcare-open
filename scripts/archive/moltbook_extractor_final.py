#!/usr/bin/env python3
"""
Moltbook 数据提取器 v3.0 - 最终版
成功提取用户主页帖子数据
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright


async def extract_moltbook_data(username="LinLin_v1"):
    """提取 Moltbook 用户数据"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://www.moltbook.com/u/{username}"
        print(f"[INFO] 访问: {url}")
        
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # 获取所有包含 /post/ 的链接
        links = await page.query_selector_all('a')
        
        posts = []
        seen_ids = set()
        
        for link in links:
            try:
                href = await link.get_attribute('href')
                if not href or '/post/' not in href:
                    continue
                    
                post_id = href.replace('/post/', '')
                if post_id in seen_ids:
                    continue
                seen_ids.add(post_id)
                
                text = await link.inner_text()
                
                # 查找包含标题和元数据的行
                lines = [l.strip() for l in text.split('\\n') if l.strip()]
                
                # 找到标题行（不包含 m/showcase 或 ▲ 或 💬 的行）
                title = None
                for line in lines:
                    if 'm/showcase' not in line and '▲' not in line and '💬' not in line and len(line) > 10:
                        title = line[:200]
                        break
                
                if not title:
                    continue
                
                # 解析时间和点赞/评论
                time_match = re.search(r'•\\s*([\\d/]+,\\s*[\\d:]+\\s*[AP]M)', text)
                time_str = time_match.group(1) if time_match else None
                
                # 提取点赞数 ▲ 1
                upvote_match = re.search(r'▲\\s*(\\d+)', text)
                likes = int(upvote_match.group(1)) if upvote_match else 0
                
                # 提取评论数 💬 1  
                comment_match = re.search(r'💬\\s*(\\d+)', text)
                comments = int(comment_match.group(1)) if comment_match else 0
                
                posts.append({
                    "post_id": post_id,
                    "title": title,
                    "submolt": "m/showcase",
                    "publish_time": time_str,
                    "likes": likes,
                    "comments": comments,
                    "url": f"https://www.moltbook.com{href}"
                })
            except Exception as e:
                pass
        
        # 截图
        screenshot_path = f"moltbook_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        
        await browser.close()
        
        result = {
            "username": username,
            "url": url,
            "extraction_time": datetime.now().isoformat(),
            "total_posts": len(posts),
            "posts": posts,
            "screenshot": screenshot_path
        }
        
        with open("moltbook_data.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"[SUCCESS] 提取完成: {len(posts)} 个帖子")
        print(f"[SUCCESS] 截图: {screenshot_path}")
        print(f"[SUCCESS] 数据: moltbook_data.json")
        
        return result


if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "LinLin_v1"
    result = asyncio.run(extract_moltbook_data(username))
    
    print("\\n=== 提取结果 ===")
    print(f"用户: {result['username']}")
    print(f"帖子数: {result['total_posts']}")
    for i, post in enumerate(result['posts'], 1):
        print(f"\\n[{i}] {post['title']}")
        print(f"    点赞: {post['likes']} | 评论: {post['comments']} | 时间: {post['publish_time']}")
