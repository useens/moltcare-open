#!/usr/bin/env python3
"""
Moltbook 超级提取器 v5.0 - 全功能优化版
并发 + 智能等待 + 增量 + 滚动 + 登录态
Token成本最低，全部本地化执行
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page

# 配置
CONFIG = {
    "username": "LinLin_v1",
    "concurrent_limit": 3,  # 并发数
    "max_scrolls": 5,       # 最大滚动次数
    "scroll_delay": 1000,   # 滚动间隔(ms)
    "data_dir": "data/moltbook",
    "cookie_file": "data/moltbook/cookies.json",
    "state_file": "data/moltbook/last_state.json"
}


class MoltbookSuperExtractor:
    def __init__(self):
        self.data_dir = Path(CONFIG["data_dir"])
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(CONFIG["concurrent_limit"])
        
    def load_cookies(self):
        """加载保存的登录态"""
        cookie_path = Path(CONFIG["cookie_file"])
        if cookie_path.exists():
            with open(cookie_path, 'r') as f:
                return json.load(f)
        return None
    
    def save_cookies(self, cookies):
        """保存登录态"""
        with open(CONFIG["cookie_file"], 'w') as f:
            json.dump(cookies, f)
    
    def load_last_state(self):
        """加载上次状态（用于增量）"""
        state_path = Path(CONFIG["state_file"])
        if state_path.exists():
            with open(state_path, 'r') as f:
                return json.load(f)
        return {"extracted_posts": []}
    
    def save_state(self, post_ids):
        """保存当前状态"""
        with open(CONFIG["state_file"], 'w') as f:
            json.dump({
                "last_update": datetime.now().isoformat(),
                "extracted_posts": post_ids
            }, f)
    
    async def scroll_to_load(self, page: Page):
        """智能滚动加载更多内容"""
        posts_before = 0
        for i in range(CONFIG["max_scrolls"]):
            # 获取当前帖子数
            links = await page.query_selector_all('a[href^="/post/"]')
            posts_now = len(set([await l.get_attribute('href') for l in links]))
            
            if posts_now == posts_before:
                print(f"[滚动] 第{i+1}次: 无新内容，停止")
                break
            
            posts_before = posts_now
            print(f"[滚动] 第{i+1}次: 当前{posts_now}个帖子")
            
            # 滚动到底部
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(CONFIG["scroll_delay"])
    
    async def extract_post_detail(self, browser, post_url: str) -> dict:
        """提取单个帖子详情（带并发控制）"""
        async with self.semaphore:  # 限制并发
            page = await browser.new_page()
            try:
                await page.goto(post_url, wait_until="networkidle", timeout=30000)
                
                # 智能等待：等文章内容出现
                try:
                    await page.wait_for_selector('[class*="content"], article, main', timeout=5000)
                except:
                    pass  # 超时继续
                
                # 提取完整内容
                content = await page.evaluate('''() => {
                    const selectors = ['[class*="content"]', '[class*="body"]', 'article', 'main', '.post'];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.innerText.length > 50) return el.innerText.substring(0, 2000);
                    }
                    return document.body.innerText.substring(0, 1000);
                }''')
                
                # 提取评论
                comments = await page.evaluate('''() => {
                    const comments = document.querySelectorAll('[class*="comment"]');
                    return Array.from(comments).slice(0, 5).map(c => ({
                        author: c.querySelector('[class*="author"]')?.innerText?.substring(0, 50),
                        text: c.innerText?.substring(0, 200)
                    }));
                }''')
                
                return {
                    "url": post_url,
                    "content": content[:500] if content else None,
                    "comments": comments,
                    "extracted_at": datetime.now().isoformat()
                }
            finally:
                await page.close()
    
    async def extract_profile(self, username: str) -> list:
        """提取用户主页帖子列表"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            # 加载cookie（如果有）
            cookies = self.load_cookies()
            if cookies:
                await context.add_cookies(cookies)
            
            page = await context.new_page()
            
            profile_url = f"https://www.moltbook.com/u/{username}"
            print(f"[主页] 访问: {profile_url}")
            
            await page.goto(profile_url, wait_until="networkidle", timeout=30000)
            
            # 智能等待：等帖子加载
            try:
                await page.wait_for_selector('a[href^="/post/"]', timeout=5000)
            except:
                print("[主页] 未找到帖子")
                return []
            
            # 滚动加载更多
            await self.scroll_to_load(page)
            
            # 提取所有帖子链接
            links = await page.query_selector_all('a[href^="/post/"]')
            post_urls = []
            seen = set()
            
            for link in links:
                href = await link.get_attribute('href')
                if href and href not in seen:
                    seen.add(href)
                    post_urls.append(f"https://www.moltbook.com{href}")
            
            print(f"[主页] 找到 {len(post_urls)} 个帖子")
            
            # 保存cookie（保持登录态）
            cookies = await context.cookies()
            self.save_cookies(cookies)
            
            await browser.close()
            return post_urls
    
    async def run(self, username: str = None):
        """主运行流程"""
        username = username or CONFIG["username"]
        
        print(f"\n{'='*50}")
        print(f"Moltbook 超级提取器 v5.0")
        print(f"用户: {username}")
        print(f"{'='*50}\n")
        
        # 1. 加载上次状态（增量）
        last_state = self.load_last_state()
        already_extracted = set(last_state.get("extracted_posts", []))
        print(f"[增量] 已提取过 {len(already_extracted)} 个帖子")
        
        # 2. 提取主页帖子列表
        post_urls = await self.extract_profile(username)
        
        # 3. 过滤新帖子
        new_urls = [url for url in post_urls if url not in already_extracted]
        print(f"[增量] 新帖子: {len(new_urls)} 个")
        
        if not new_urls:
            print("[完成] 没有新帖子需要提取")
            return
        
        # 4. 并发提取详情
        print(f"[并发] 启动 {CONFIG['concurrent_limit']} 个并发任务\n")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            tasks = [self.extract_post_detail(browser, url) for url in new_urls[:10]]  # 限制前10个
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            await browser.close()
        
        # 5. 处理结果
        successful = [r for r in results if isinstance(r, dict)]
        errors = [r for r in results if isinstance(r, Exception)]
        
        # 6. 保存数据
        output_file = self.data_dir / f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "username": username,
                "extraction_time": datetime.now().isoformat(),
                "new_posts_count": len(successful),
                "errors_count": len(errors),
                "posts": successful
            }, f, ensure_ascii=False, indent=2)
        
        # 7. 更新状态
        all_extracted = already_extracted.union(set(new_urls[:len(successful)]))
        self.save_state(list(all_extracted))
        
        # 8. 输出摘要（供AI查看）
        print(f"\n{'='*50}")
        print(f"提取完成")
        print(f"{'='*50}")
        print(f"新帖子: {len(successful)}")
        print(f"失败: {len(errors)}")
        print(f"数据保存: {output_file}")
        
        for i, post in enumerate(successful[:3], 1):
            print(f"\n[{i}] {post['url'][:60]}...")
            print(f"    内容: {post['content'][:100]}..." if post['content'] else "    内容: N/A")
            print(f"    评论数: {len(post['comments'])}")
        
        return output_file


if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else None
    
    extractor = MoltbookSuperExtractor()
    result = asyncio.run(extractor.run(username))
