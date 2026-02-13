#!/usr/bin/env python3
"""
Moltbook 提取器 v6.0
基于 BaseWebExtractor，使用通用框架重构
"""

import asyncio
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from base_extractor import BaseWebExtractor
from playwright.async_api import Page


class MoltbookExtractor(BaseWebExtractor):
    """Moltbook 社区提取器"""
    
    def __init__(self, username: str = "LinLin_v1"):
        super().__init__(
            name="moltbook",
            base_url="https://www.moltbook.com",
            data_dir="data/moltbook",
            concurrent_limit=3,
            max_scrolls=5,
            scroll_delay=1000,
            headless=True
        )
        self.username = username
    
    def get_selectors(self) -> dict:
        """Moltbook CSS 选择器"""
        return {
            'item': 'a[href^="/post/"]',
            'title': 'h1, h2, h3',
            'content': '[class*="content"], article',
            'author': '[class*="author"], [href^="/u/"]',
            'time': 'time',
            'votes': '[class*="vote"], [class*="score"]',
        }
    
    async def parse_item(self, element, page: Page) -> dict:
        """解析 Moltbook 帖子元素"""
        try:
            # 获取链接
            href = await element.get_attribute('href')
            if not href:
                return None
            
            url = f"{self.base_url}{href}" if href.startswith('/') else href
            
            # 获取标题（从父元素或兄弟元素）
            title = ""
            parent = await element.evaluate('el => el.closest("article, .post, [class*=\'post\']")')
            if parent:
                title_elem = await page.query_selector('h1, h2, h3, [class*="title"]')
                if title_elem:
                    title = await title_elem.inner_text()
            
            return {
                'url': url,
                'title': title.strip()[:200],
                'post_id': href.split('/')[-1] if '/' in href else href,
            }
        except Exception as e:
            print(f"[解析错误] {e}")
            return None
    
    async def extract_post_content(self, url: str) -> dict:
        """提取帖子详情内容"""
        async def extract_fn(page: Page):
            # 等待内容加载
            try:
                await page.wait_for_selector('[class*="content"], article, main', timeout=3000)
            except:
                pass
            
            # 提取内容
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
                'content': content[:500] if content else None,
                'comments': comments,
            }
        
        return await self.extract_detail(url, extract_fn)
    
    async def extract_profile(self) -> list:
        """提取用户主页帖子"""
        url = f"{self.base_url}/u/{self.username}"
        print(f"\n{'='*50}")
        print(f"Moltbook 提取器 v6.0")
        print(f"用户: {self.username}")
        print(f"{'='*50}\n")
        
        # 增量提取
        items = await self.run_incremental(url, id_key='url')
        
        if not items:
            print("[完成] 没有新帖子")
            return []
        
        # 提取详情
        print(f"[详情] 提取 {len(items)} 个帖子内容...")
        detailed_items = []
        
        for item in items:
            detail = await self.extract_post_content(item['url'])
            if detail:
                item.update(detail)
                detailed_items.append(item)
        
        # 保存结果
        self.save_results(detailed_items, f"{self.username}_profile")
        
        print(f"\n{'='*50}")
        print(f"提取完成: {len(detailed_items)} 个新帖子")
        print(f"{'='*50}")
        
        return detailed_items
    
    async def extract_hot(self, limit: int = 10) -> list:
        """提取热门帖子"""
        url = f"{self.base_url}/?sort=hot"
        print(f"\n{'='*50}")
        print(f"Moltbook 热门帖子提取")
        print(f"{'='*50}\n")
        
        # 提取列表
        items = await self.extract_list(url)
        items = items[:limit]
        
        print(f"[详情] 提取 {len(items)} 个帖子内容...")
        detailed_items = []
        
        # 修复: 使用asyncio.wait_for添加超时保护
        for i, item in enumerate(items):
            print(f"  [{i+1}/{len(items)}] 提取: {item.get('title', '无标题')[:40]}...")
            try:
                detail = await asyncio.wait_for(
                    self.extract_post_content(item['url']),
                    timeout=20  # 单个帖子20秒超时
                )
                if detail:
                    item.update(detail)
                    detailed_items.append(item)
            except asyncio.TimeoutError:
                print(f"    ⚠️ 超时跳过")
            except Exception as e:
                print(f"    ⚠️ 错误: {e}")
        
        # 保存结果
        self.save_results(detailed_items, "hot")
        
        # 输出摘要
        print(f"\n{'='*50}")
        print(f"提取完成: {len(detailed_items)} 个热门帖子")
        print(f"{'='*50}")
        
        for i, item in enumerate(detailed_items[:5], 1):
            print(f"\n[{i}] {item.get('title', '无标题')[:60]}...")
            content = item.get('content', '')
            if content:
                print(f"    {content[:100]}...")
        
        return detailed_items


async def main():
    """命令行入口"""
    extractor = MoltbookExtractor()
    
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == "hot":
                await asyncio.wait_for(extractor.extract_hot(), timeout=120)  # 2分钟总超时
            elif sys.argv[1] == "profile":
                extractor.username = sys.argv[2] if len(sys.argv) > 2 else "LinLin_v1"
                await asyncio.wait_for(extractor.extract_profile(), timeout=120)
            else:
                extractor.username = sys.argv[1]
                await asyncio.wait_for(extractor.extract_profile(), timeout=120)
        else:
            await asyncio.wait_for(extractor.extract_profile(), timeout=120)
    except asyncio.TimeoutError:
        print("\n[错误] 提取超时（2分钟），请重试")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[中断] 用户取消")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
