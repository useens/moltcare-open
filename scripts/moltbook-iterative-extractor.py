#!/usr/bin/env python3
"""
Moltbook 迭代提取器 v1.0
访问主页 → 提取帖子列表 → 点击每个帖子 → 提取详情 → 返回
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright


async def extract_post_detail(page, post_url):
    """提取单个帖子详情"""
    await page.goto(post_url, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(2000)
    
    # 提取完整内容
    content = await page.evaluate('''() => {
        // 尝试多种选择器找内容
        const selectors = [
            '[class*="content"]',
            '[class*="body"]',
            'article',
            'main'
        ];
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el) return el.innerText.substring(0, 1000);
        }
        return document.body.innerText.substring(0, 500);
    }''')
    
    # 提取评论数（详情页可能显示更多）
    comments_text = await page.evaluate('''() => {
        const comments = document.querySelectorAll('[class*="comment"]');
        return comments.length;
    }''')
    
    return {
        "url": post_url,
        "content_preview": content[:200] if content else None,
        "comments_count": comments_text
    }


async def extract_with_iteration(username="LinLin_v1"):
    """迭代提取：主页→帖子列表→每个帖子详情"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        results = {
            "username": username,
            "extraction_time": datetime.now().isoformat(),
            "posts": []
        }
        
        # Step 1: 访问主页，提取帖子列表
        profile_url = f"https://www.moltbook.com/u/{username}"
        print(f"[Step 1] 访问主页: {profile_url}")
        
        await page.goto(profile_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # 提取帖子链接
        links = await page.query_selector_all('a[href^="/post/"]')
        post_urls = []
        seen = set()
        
        for link in links:
            href = await link.get_attribute('href')
            if href and href not in seen:
                seen.add(href)
                post_urls.append(f"https://www.moltbook.com{href}")
        
        print(f"[Step 1] 发现 {len(post_urls)} 个帖子")
        
        # Step 2: 遍历每个帖子，提取详情
        for i, post_url in enumerate(post_urls[:3], 1):  # 限制前3个避免耗时过长
            print(f"[Step 2.{i}] 访问帖子详情: {post_url}")
            
            try:
                detail = await extract_post_detail(page, post_url)
                results["posts"].append(detail)
                print(f"[Step 2.{i}] ✓ 提取成功")
            except Exception as e:
                print(f"[Step 2.{i}] ✗ 提取失败: {e}")
        
        # Step 3: 返回主页（可选）
        print("[Step 3] 返回主页")
        await page.goto(profile_url, wait_until="networkidle", timeout=30000)
        
        # 最终截图
        screenshot = f"moltbook_iter_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=screenshot, full_page=True)
        
        await browser.close()
        
        results["screenshot"] = screenshot
        
        # 保存结果
        with open("moltbook_iter_data.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return results


if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "LinLin_v1"
    
    result = asyncio.run(extract_with_iteration(username))
    
    print(f"\n=== 迭代提取完成 ===")
    print(f"用户: {result['username']}")
    print(f"详情页数: {len(result['posts'])}")
    
    for i, p in enumerate(result['posts'], 1):
        print(f"\n[{i}] {p['url']}")
        print(f"    内容: {p['content_preview'][:80]}...")
        print(f"    评论元素: {p['comments_count']}")
    
    print(f"\n截图: {result['screenshot']}")
