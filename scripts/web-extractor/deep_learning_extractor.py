#!/usr/bin/env python3
"""
深度内容提取器 v2.1 - 修复版
使用系统Chromium，修复浏览器配置问题
不只是标题，要点进去看完整内容
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 修复：配置Playwright使用系统Chromium
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/usr/bin/chromium"
os.environ["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"

sys.path.insert(0, str(Path(__file__).parent))

from generic_extractor import GenericExtractor
from base_extractor import BaseWebExtractor
from playwright.async_api import async_playwright, Page

# 全局配置
CHROMIUM_PATH = "/usr/bin/chromium"


class DeepLearningExtractor(BaseWebExtractor):
    """深度提取器 - 访问详情页获取完整内容"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        super().__init__(
            name=self.config['name'],
            base_url=self.config['base_url'],
            data_dir=self.config.get('data_dir', f"data/{self.config['name']}_deep"),
            concurrent_limit=self.config.get('concurrent_limit', 3),
            max_scrolls=3,
            scroll_delay=1500,
            headless=True
        )
        self.config_path = config_path
        self.processed_urls = set()
    
    def get_selectors(self) -> dict:
        return self.config.get('selectors', {})
    
    async def parse_item(self, element, page: Page) -> dict:
        """解析列表项，获取标题和详情页链接"""
        try:
            # 获取标题
            title_sel = self.config['fields']['title']['selector']
            title_elem = await element.query_selector(title_sel)
            title = await title_elem.inner_text() if title_elem else ""
            
            # 获取链接
            link_sel = self.config['fields']['url']['selector']
            link_elem = await element.query_selector(link_sel)
            href = await link_elem.get_attribute('href') if link_elem else ""
            
            if href.startswith('/'):
                href = f"{self.base_url}{href}"
            elif not href.startswith('http'):
                href = f"{self.base_url}/{href}"
            
            # 获取评论数/互动数（用于优先级排序）
            comments = ""
            if 'comments_url' in self.config['fields']:
                comm_sel = self.config['fields']['comments_url']['selector']
                comm_elem = await element.query_selector(comm_sel)
                if comm_elem:
                    comm_text = await comm_elem.inner_text()
                    comments = comm_text.strip()
            
            return {
                'title': title.strip()[:200],
                'url': href,
                'comments': comments,
                'source': self.config['name']
            }
        except Exception as e:
            return None
    
    async def extract_detail_content(self, url: str, title: str) -> dict:
        """访问详情页，提取完整内容"""
        async with self.semaphore:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
                page = await browser.new_page()
                
                try:
                    print(f"  📖 深入学习: {title[:60]}...")
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    # 等待内容加载
                    await page.wait_for_timeout(2000)
                    
                    # 根据来源使用不同的提取策略
                    content = ""
                    
                    if 'moltbook' in self.config['name']:
                        # Moltbook 内容提取
                        content = await page.evaluate('''() => {
                            const selectors = ['[class*="content"]', 'article', '.post-content', 'main'];
                            for (const sel of selectors) {
                                const el = document.querySelector(sel);
                                if (el && el.innerText.length > 100) return el.innerText.substring(0, 3000);
                            }
                            return document.body.innerText.substring(0, 2000);
                        }''')
                    
                    elif 'hackernews' in self.config['name']:
                        # HN 评论提取
                        content = await page.evaluate('''() => {
                            const comments = document.querySelectorAll('.commtext');
                            let text = '';
                            comments.forEach((c, i) => {
                                if (i < 5) text += c.innerText + '\n\n';
                            });
                            return text.substring(0, 3000) || document.querySelector('.fatitem')?.innerText?.substring(0, 2000);
                        }''')
                    
                    elif 'github' in self.config['name']:
                        # GitHub README提取
                        content = await page.evaluate('''() => {
                            const readme = document.querySelector('[data-testid="readme"]');
                            if (readme) return readme.innerText.substring(0, 3000);
                            const article = document.querySelector('article');
                            if (article) return article.innerText.substring(0, 3000);
                            return document.body.innerText.substring(0, 2000);
                        }''')
                    
                    else:
                        # 通用内容提取
                        content = await page.evaluate('''() => {
                            const selectors = ['article', '[class*="content"]', '[class*="body"]', 'main', '.post'];
                            for (const sel of selectors) {
                                const el = document.querySelector(sel);
                                if (el && el.innerText.length > 200) return el.innerText.substring(0, 3000);
                            }
                            return document.body.innerText.substring(0, 2000);
                        }''')
                    
                    # 提取评论
                    comments = await page.evaluate('''() => {
                        const commentSelectors = ['[class*="comment"]', '.comment', '[class*="reply"]'];
                        for (const sel of commentSelectors) {
                            const elems = document.querySelectorAll(sel);
                            if (elems.length > 0) {
                                return Array.from(elems).slice(0, 3).map(c => c.innerText?.substring(0, 300));
                            }
                        }
                        return [];
                    }''')
                    
                    await browser.close()
                    
                    return {
                        'url': url,
                        'title': title,
                        'content': content[:2000] if content else "",
                        'comments': comments[:3],
                        'word_count': len(content.split()) if content else 0,
                        'extracted_at': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    print(f"  ⚠️  提取失败 {url}: {e}")
                    await browser.close()
                    return None
    
    async def collect_with_deep_learning(self, url: str = None, max_deep_extract: int = 3) -> list:
        """
        收集并深度学习 - 用于进化脚本
        
        Args:
            url: 起始URL（可选，使用配置文件中的）
            max_deep_extract: 最大深度提取数量
            
        Returns:
            列表项，包含深度内容（如果有）
        """
        start_url = url or self.config.get('start_url', self.base_url)
        
        # 1. 获取列表
        list_items = await self.extract_list(start_url)
        
        if not list_items:
            return []
        
        # 2. 为每个项目添加互动数（用于排序）
        for item in list_items:
            comm = item.get('comments', '')
            nums = ''.join(filter(str.isdigit, comm))
            item['interaction_count'] = int(nums) if nums else 0
        
        # 3. 按互动数排序
        sorted_items = sorted(list_items, key=lambda x: x.get('interaction_count', 0), reverse=True)
        
        # 4. 对前N个进行深度提取
        top_items = sorted_items[:max_deep_extract]
        
        for item in top_items:
            detail_url = item.get('url', '')
            title = item.get('title', '')
            
            if detail_url and detail_url not in self.processed_urls:
                detail = await self.extract_detail_content(detail_url, title)
                if detail:
                    item['deep_content'] = detail.get('content', '')
                    item['deep_comments'] = detail.get('comments', [])
                    item['word_count'] = detail.get('word_count', 0)
                    self.processed_urls.add(detail_url)
        
        return sorted_items
    
    async def deep_extract(self, limit: int = 5) -> list:
        """
        深度提取流程：
        1. 获取列表
        2. 按互动数排序
        3. 访问详情页获取完整内容
        """
        print(f"\n{'='*60}")
        print(f"🔬 深度提取: {self.config['name']}")
        print(f"目标: 深入学习 {limit} 个热门内容")
        print(f"{'='*60}\n")
        
        # 1. 获取列表
        list_items = await self.extract_list(self.config.get('start_url', self.base_url))
        print(f"📋 获取 {len(list_items)} 个列表项\n")
        
        if not list_items:
            print("❌ 没有获取到列表")
            return []
        
        # 2. 按互动数排序（优先学习热门内容）
        def get_interaction_count(item):
            comm = item.get('comments', '')
            nums = ''.join(filter(str.isdigit, comm))
            return int(nums) if nums else 0
        
        sorted_items = sorted(list_items, key=get_interaction_count, reverse=True)
        top_items = sorted_items[:limit]
        
        print(f"🎯 选择前 {len(top_items)} 个热门内容深入学习:\n")
        for i, item in enumerate(top_items, 1):
            print(f"  {i}. {item.get('title', '无标题')[:50]}...")
            print(f"     💬 {item.get('comments', '0 comments')}")
        
        # 3. 访问详情页获取完整内容
        print(f"\n📖 开始深入学习...\n")
        detailed_items = []
        
        for item in top_items:
            url = item.get('url', '')
            title = item.get('title', '')
            
            if url and url not in self.processed_urls:
                detail = await self.extract_detail_content(url, title)
                if detail and detail.get('content'):
                    detailed_items.append(detail)
                    self.processed_urls.add(url)
                    print(f"     ✅ 成功提取 {detail.get('word_count', 0)} 词\n")
                else:
                    print(f"     ⚠️  内容为空\n")
        
        # 4. 保存结果
        output_file = self.save_results(detailed_items, "deep_learning")
        
        # 5. 输出摘要
        print(f"{'='*60}")
        print(f"📊 深度学习完成")
        print(f"{'='*60}")
        print(f"深入学习: {len(detailed_items)} 个内容")
        print(f"总词数: {sum(item.get('word_count', 0) for item in detailed_items)}")
        print(f"保存至: {output_file}")
        
        # 显示第一个内容的预览
        if detailed_items:
            first = detailed_items[0]
            print(f"\n📖 第一个内容预览:")
            print(f"标题: {first.get('title', 'N/A')[:60]}...")
            content_preview = first.get('content', '')[:300]
            print(f"内容: {content_preview}...")
        
        return detailed_items


async def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("深度内容提取器 - 深入学习模式")
        print()
        print("用法:")
        print(f"  python3 {sys.argv[0]} <config.json> [limit]")
        print()
        print("示例:")
        print(f"  python3 {sys.argv[0]} configs/moltbook.json 5")
        print(f"  python3 {sys.argv[0]} configs/hackernews.json 3")
        return
    
    config_path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    if not Path(config_path).exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return
    
    extractor = DeepLearningExtractor(config_path)
    await extractor.deep_extract(limit=limit)


if __name__ == "__main__":
    asyncio.run(main())
