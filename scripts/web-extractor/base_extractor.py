#!/usr/bin/env python3
"""
通用网页提取器基础类 v1.0
支持：智能滚动、并发提取、登录态管理、增量提取
适用于：任何基于 Playwright 的动态网页提取
"""

import asyncio
import json
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
from playwright.async_api import async_playwright, Page, Browser


class BaseWebExtractor(ABC):
    """
    通用网页提取器基类
    
    子类需要实现：
    - get_selectors(): 返回 CSS 选择器配置
    - parse_item(element): 解析单个元素为数据字典
    - get_login_url(): 返回登录页面 URL（可选）
    """
    
    def __init__(
        self,
        name: str,
        base_url: str,
        data_dir: str = "data/extractor",
        concurrent_limit: int = 3,
        max_scrolls: int = 5,
        scroll_delay: int = 1000,
        headless: bool = True
    ):
        self.name = name
        self.base_url = base_url.rstrip('/')
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.concurrent_limit = concurrent_limit
        self.max_scrolls = max_scrolls
        self.scroll_delay = scroll_delay
        self.headless = headless
        
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        self.cookies_file = self.data_dir / f"{name}_cookies.json"
        self.state_file = self.data_dir / f"{name}_state.json"
    
    @abstractmethod
    def get_selectors(self) -> Dict[str, str]:
        """
        返回 CSS 选择器配置
        
        Returns:
            {
                'item': 'article.post',  # 列表项选择器
                'title': 'h2.title',     # 标题选择器
                'link': 'a.post-link',   # 链接选择器
                'content': '.content',   # 内容选择器
                'author': '.author',     # 作者选择器
                'time': 'time',          # 时间选择器
            }
        """
        pass
    
    @abstractmethod
    async def parse_item(self, element, page: Page) -> Optional[Dict]:
        """
        解析单个元素为数据字典
        
        Args:
            element: Playwright ElementHandle
            page: Playwright Page
            
        Returns:
            数据字典或 None（如果解析失败）
        """
        pass
    
    def get_login_url(self) -> Optional[str]:
        """返回登录页面 URL（可选）"""
        return None
    
    def load_cookies(self) -> Optional[List[Dict]]:
        """加载保存的 cookies"""
        if self.cookies_file.exists():
            with open(self.cookies_file, 'r') as f:
                return json.load(f)
        return None
    
    def save_cookies(self, cookies: List[Dict]):
        """保存 cookies"""
        with open(self.cookies_file, 'w') as f:
            json.dump(cookies, f)
    
    def load_state(self) -> Dict:
        """加载上次提取状态（用于增量）"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {"extracted_ids": [], "last_update": None}
    
    def save_state(self, extracted_ids: List[str]):
        """保存提取状态"""
        with open(self.state_file, 'w') as f:
            json.dump({
                "last_update": datetime.now().isoformat(),
                "extracted_ids": extracted_ids
            }, f)
    
    def generate_id(self, url: str) -> str:
        """生成唯一 ID（用于去重）"""
        return hashlib.md5(url.encode()).hexdigest()[:16]
    
    async def smart_scroll(self, page: Page, selector: str):
        """
        智能滚动加载更多内容
        
        Args:
            page: Playwright Page
            selector: 要监控的元素选择器
        """
        items_before = 0
        
        for i in range(self.max_scrolls):
            # 获取当前元素数量
            items = await page.query_selector_all(selector)
            items_now = len(items)
            
            if items_now == items_before:
                print(f"[滚动] 第{i+1}次: 无新内容，停止")
                break
            
            items_before = items_now
            print(f"[滚动] 第{i+1}次: 当前{items_now}个元素")
            
            # 滚动到底部
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(self.scroll_delay)
    
    async def extract_list(
        self,
        url: str,
        use_cookies: bool = True
    ) -> List[Dict]:
        """
        提取列表页面
        
        Args:
            url: 列表页面 URL
            use_cookies: 是否使用保存的 cookies
            
        Returns:
            提取的数据列表
        """
        selectors = self.get_selectors()
        items = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            
            # 加载 cookies
            if use_cookies:
                cookies = self.load_cookies()
                if cookies:
                    await context.add_cookies(cookies)
            
            page = await context.new_page()
            
            print(f"[访问] {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 等待列表加载
            try:
                await page.wait_for_selector(selectors['item'], timeout=10000)
            except:
                print(f"[警告] 未找到列表元素: {selectors['item']}")
                await browser.close()
                return items
            
            # 滚动加载更多
            await self.smart_scroll(page, selectors['item'])
            
            # 提取所有列表项
            elements = await page.query_selector_all(selectors['item'])
            print(f"[提取] 找到 {len(elements)} 个元素")
            
            for element in elements:
                try:
                    data = await self.parse_item(element, page)
                    if data:
                        items.append(data)
                except Exception as e:
                    print(f"[错误] 解析元素失败: {e}")
                    continue
            
            # 保存 cookies
            if use_cookies:
                cookies = await context.cookies()
                self.save_cookies(cookies)
            
            await browser.close()
        
        return items
    
    async def extract_detail(
        self,
        url: str,
        extract_fn: Callable[[Page], Dict]
    ) -> Optional[Dict]:
        """
        提取详情页面（带并发控制）
        
        Args:
            url: 详情页面 URL
            extract_fn: 提取函数，接收 page 返回字典
            
        Returns:
            提取的数据或 None
        """
        async with self.semaphore:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    data = await extract_fn(page)
                    data['url'] = url
                    data['extracted_at'] = datetime.now().isoformat()
                    return data
                except Exception as e:
                    print(f"[错误] 提取详情失败 {url}: {e}")
                    return None
                finally:
                    await browser.close()
    
    async def run_incremental(
        self,
        url: str,
        id_key: str = 'url'
    ) -> List[Dict]:
        """
        增量提取（只提取新内容）
        
        Args:
            url: 列表页面 URL
            id_key: 用于去重的字段名
            
        Returns:
            新提取的数据列表
        """
        # 加载上次状态
        state = self.load_state()
        already_extracted = set(state.get("extracted_ids", []))
        print(f"[增量] 已提取过 {len(already_extracted)} 条")
        
        # 提取列表
        items = await self.extract_list(url)
        
        # 过滤新内容
        new_items = []
        for item in items:
            item_id = self.generate_id(item.get(id_key, ''))
            if item_id not in already_extracted:
                new_items.append(item)
        
        print(f"[增量] 新内容: {len(new_items)} 条")
        
        # 保存状态
        all_ids = already_extracted.union(
            set(self.generate_id(item.get(id_key, '')) for item in new_items)
        )
        self.save_state(list(all_ids))
        
        return new_items
    
    def save_results(self, items: List[Dict], suffix: str = ""):
        """
        保存结果到文件
        
        Args:
            items: 数据列表
            suffix: 文件名后缀
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.name}_{suffix}_{timestamp}.json" if suffix else f"{self.name}_{timestamp}.json"
        output_file = self.data_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "extractor": self.name,
                "base_url": self.base_url,
                "extraction_time": datetime.now().isoformat(),
                "count": len(items),
                "items": items
            }, f, ensure_ascii=False, indent=2)
        
        print(f"[保存] {output_file}")
        return output_file


# 使用示例：创建具体提取器
class ExampleExtractor(BaseWebExtractor):
    """示例提取器 - 展示如何实现具体平台"""
    
    def get_selectors(self) -> Dict[str, str]:
        return {
            'item': 'article.post',
            'title': 'h2.title',
            'link': 'a.post-link',
            'content': '.content',
            'author': '.author',
            'time': 'time',
        }
    
    async def parse_item(self, element, page: Page) -> Optional[Dict]:
        try:
            title_elem = await element.query_selector('h2.title')
            title = await title_elem.inner_text() if title_elem else ""
            
            link_elem = await element.query_selector('a.post-link')
            href = await link_elem.get_attribute('href') if link_elem else ""
            
            return {
                'title': title.strip(),
                'url': self.base_url + href if href.startswith('/') else href,
            }
        except:
            return None


if __name__ == "__main__":
    # 示例用法
    print("通用网页提取器基础类 v1.0")
    print("使用方法：继承 BaseWebExtractor 并实现抽象方法")
    print()
    print("示例：")
    print("  class MyExtractor(BaseWebExtractor):")
    print("      def get_selectors(self): ...")
    print("      async def parse_item(self, element, page): ...")
