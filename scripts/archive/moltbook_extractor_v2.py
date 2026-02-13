#!/usr/bin/env python3
"""
Moltbook 数据提取器 v2.0 - 简化版
直接使用 JavaScript 在页面内提取数据
"""

import asyncio
import json
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
        await page.wait_for_timeout(3000)  # 等待JS渲染
        
        # 使用 JavaScript 提取数据
        posts_data = await page.evaluate('''() => {
            const posts = [];
            
            // 查找所有帖子元素 - 尝试多种选择器
            const postElements = document.querySelectorAll('article, [class*="post"], [class*="card"], .feed-item');
            
            postElements.forEach((el, index) => {
                try {
                    // 提取标题
                    const titleEl = el.querySelector('h1, h2, h3, h4, [class*="title"], a');
                    const title = titleEl ? titleEl.innerText.trim() : null;
                    
                    // 提取点赞数 - 查找包含数字和"赞"或向上箭头的元素
                    const likesEl = el.querySelector('[class*="like"], [class*="upvote"], button');
                    let likes = null;
                    if (likesEl) {
                        const text = likesEl.innerText || likesEl.textContent;
                        const match = text.match(/\\d+/);
                        likes = match ? parseInt(match[0]) : null;
                    }
                    
                    // 提取评论数
                    const commentsEl = el.querySelector('[class*="comment"]');
                    let comments = null;
                    if (commentsEl) {
                        const text = commentsEl.innerText || commentsEl.textContent;
                        const match = text.match(/\\d+/);
                        comments = match ? parseInt(match[0]) : null;
                    }
                    
                    // 提取时间
                    const timeEl = el.querySelector('time, [datetime], [class*="time"], [class*="date"]');
                    const publishTime = timeEl ? timeEl.getAttribute('datetime') || timeEl.innerText : null;
                    
                    if (title && title.length > 5) {
                        posts.push({
                            index: index + 1,
                            title: title.substring(0, 200),
                            likes: likes,
                            comments: comments,
                            publish_time: publishTime
                        });
                    }
                } catch (e) {
                    console.error('提取错误:', e);
                }
            });
            
            return posts;
        }''')
        
        # 截图保存
        screenshot_path = f"moltbook_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        
        await browser.close()
        
        result = {
            "username": username,
            "url": url,
            "extraction_time": datetime.now().isoformat(),
            "total_posts": len(posts_data),
            "posts": posts_data,
            "screenshot": screenshot_path
        }
        
        # 保存JSON
        with open("moltbook_data.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"[SUCCESS] 提取完成: {len(posts_data)} 个帖子")
        print(f"[SUCCESS] 截图保存: {screenshot_path}")
        print(f"[SUCCESS] 数据保存: moltbook_data.json")
        
        return result


if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "LinLin_v1"
    
    result = asyncio.run(extract_moltbook_data(username))
    
    print("\\n提取摘要:")
    print(f"  总帖子数: {result['total_posts']}")
    for post in result['posts'][:3]:
        print(f"  - {post.get('title', 'N/A')[:60]}...")
