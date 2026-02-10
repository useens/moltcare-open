#!/usr/bin/env python3
"""
Moltbook 超级提取器 v2.1
基于 Playwright，支持动态加载
"""

import json
import sys
from playwright.sync_api import sync_playwright
from datetime import datetime

def extract_moltbook_posts(sort_by="new", limit=10):
    """
    提取 Moltbook 帖子
    """
    posts_data = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        
        print(f"🌐 访问 Moltbook ({sort_by})...")
        page.goto(f"https://moltbook.com/?sort={sort_by}", wait_until="networkidle", timeout=30000)
        
        # 等待初始加载
        page.wait_for_timeout(3000)
        
        # 滚动页面触发更多内容加载
        print("📜 滚动页面加载内容...")
        for _ in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
        
        # 获取页面文本内容进行分析
        page_text = page.evaluate("() => document.body.innerText")
        
        # 尝试多种选择器找帖子
        selectors = [
            "article",
            "[class*='post']",
            "[class*='Post']",
            "main > div > div > div",
            "[data-testid]",
            ".feed > div",
            "main div > a[href^='/p/']",
        ]
        
        posts = []
        for sel in selectors:
            try:
                elems = page.query_selector_all(sel)
                if len(elems) > 3:  # 找到足够多的元素
                    posts = elems
                    print(f"✅ 使用选择器: {sel} ({len(elems)} 个元素)")
                    break
            except:
                continue
        
        if not posts:
            print("⚠️ 未找到帖子元素，尝试直接解析页面文本")
            # 从页面文本中提取帖子信息
            lines = [l.strip() for l in page_text.split('\n') if l.strip()]
            
            # 找包含 @username 的行
            for i, line in enumerate(lines[:50]):
                if '@' in line and len(line) < 100:
                    posts_data.append({
                        "index": len(posts_data) + 1,
                        "title": line,
                        "author": line.split('@')[1].split()[0] if '@' in line else "",
                        "time": "",
                        "content": "",
                        "votes": "",
                        "comments": ""
                    })
                    if len(posts_data) >= limit:
                        break
        else:
            # 从找到的元素中提取
            for i, post in enumerate(posts[:limit]):
                try:
                    text = post.inner_text()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    
                    if lines:
                        posts_data.append({
                            "index": i + 1,
                            "title": lines[0][:100],
                            "author": lines[1][:50] if len(lines) > 1 else "",
                            "time": "",
                            "content": "\n".join(lines[2:5]),
                            "votes": "",
                            "comments": ""
                        })
                except Exception as e:
                    continue
        
        # 截图保存
        page.screenshot(path=f'/tmp/moltbook_{sort_by}.png', full_page=True)
        
        browser.close()
    
    return posts_data

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Moltbook 超级提取器 v2.1")
    parser.add_argument("--sort", choices=["new", "top", "discussed"], default="new",
                       help="排序方式")
    parser.add_argument("--limit", type=int, default=10, help="提取数量")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    print(f"🚀 Moltbook 超级提取器 v2.1")
    print(f"📌 排序: {args.sort} | 数量: {args.limit}")
    print("=" * 50)
    
    posts = extract_moltbook_posts(args.sort, args.limit)
    
    if args.json:
        print(json.dumps(posts, ensure_ascii=False, indent=2))
    else:
        print()
        for post in posts:
            print(f"[{post['index']}] {post['title']}")
            if post['author']:
                print(f"    👤 @{post['author']}")
            if post['content']:
                print(f"    📝 {post['content'][:100]}...")
            print()
    
    # 保存到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/tmp/moltbook_{args.sort}_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已保存到: {output_file}")
    print(f"📸 截图: /tmp/moltbook_{args.sort}.png")
    print(f"📊 共提取 {len(posts)} 条帖子")

if __name__ == "__main__":
    main()
