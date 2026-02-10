#!/usr/bin/env python3
"""
通用网页提取器 v1.0
通过 JSON 配置即可适配任何网站
无需编写代码
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from base_extractor import BaseWebExtractor
from playwright.async_api import Page


class GenericExtractor(BaseWebExtractor):
    """
    通用提取器 - 通过配置文件适配任何网站
    
    配置文件格式 (JSON):
    {
        "name": "example_site",
        "base_url": "https://example.com",
        "selectors": {
            "item": "article.post",
            "title": "h2.title",
            "link": "a.read-more",
            "content": ".post-content",
            "author": ".author-name",
            "time": "time.pub-date"
        },
        "fields": {
            "title": {"selector": "h2.title", "attribute": "text"},
            "url": {"selector": "a.read-more", "attribute": "href"},
            "author": {"selector": ".author-name", "attribute": "text"}
        },
        "pagination": {
            "type": "scroll",
            "max_scrolls": 5,
            "scroll_delay": 1000
        },
        "detail_page": {
            "enabled": true,
            "content_selector": ".full-content",
            "wait_for": ".content-loaded"
        }
    }
    """
    
    def __init__(self, config_path: str):
        # 加载配置
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # 初始化基类
        super().__init__(
            name=self.config['name'],
            base_url=self.config['base_url'],
            data_dir=self.config.get('data_dir', f"data/{self.config['name']}"),
            concurrent_limit=self.config.get('concurrent_limit', 3),
            max_scrolls=self.config.get('pagination', {}).get('max_scrolls', 5),
            scroll_delay=self.config.get('pagination', {}).get('scroll_delay', 1000),
            headless=self.config.get('headless', True)
        )
        
        self.config_path = config_path
    
    def get_selectors(self) -> dict:
        """从配置返回选择器"""
        return self.config.get('selectors', {})
    
    async def parse_item(self, element, page: Page) -> dict:
        """根据配置解析元素"""
        result = {}
        fields = self.config.get('fields', {})
        
        for field_name, field_config in fields.items():
            try:
                selector = field_config.get('selector', '')
                attribute = field_config.get('attribute', 'text')
                
                elem = await element.query_selector(selector)
                if not elem:
                    result[field_name] = ""
                    continue
                
                if attribute == 'text':
                    value = await elem.inner_text()
                elif attribute == 'href':
                    value = await elem.get_attribute('href')
                    # 处理相对 URL
                    if value and value.startswith('/'):
                        value = f"{self.base_url}{value}"
                else:
                    value = await elem.get_attribute(attribute)
                
                result[field_name] = value.strip() if value else ""
                
            except Exception as e:
                print(f"[警告] 提取字段 {field_name} 失败: {e}")
                result[field_name] = ""
        
        return result
    
    async def extract_detail_content(self, url: str) -> dict:
        """提取详情页内容（如果配置启用）"""
        detail_config = self.config.get('detail_page', {})
        if not detail_config.get('enabled', False):
            return {}
        
        async def extract_fn(page: Page):
            # 等待特定元素
            wait_for = detail_config.get('wait_for')
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=5000)
                except:
                    pass
            
            # 提取内容
            content_selector = detail_config.get('content_selector', 'body')
            content = await page.evaluate(f'''() => {{
                const el = document.querySelector("{content_selector}");
                return el ? el.innerText.substring(0, 2000) : document.body.innerText.substring(0, 1000);
            }}''')
            
            return {'full_content': content}
        
        return await self.extract_detail(url, extract_fn)
    
    async def run(self, url: str = None, mode: str = "list"):
        """
        运行提取
        
        Args:
            url: 目标 URL（默认使用配置的 base_url）
            mode: list(列表页) | incremental(增量)
        """
        target_url = url or self.config.get('start_url', self.base_url)
        
        print(f"\n{'='*50}")
        print(f"通用提取器: {self.name}")
        print(f"目标: {target_url}")
        print(f"模式: {mode}")
        print(f"{'='*50}\n")
        
        if mode == "incremental":
            items = await self.run_incremental(target_url, id_key='url')
        else:
            items = await self.extract_list(target_url)
        
        if not items:
            print("[完成] 没有提取到内容")
            return []
        
        # 如果启用详情页提取
        detail_config = self.config.get('detail_page', {})
        if detail_config.get('enabled', False):
            print(f"[详情] 提取 {len(items)} 个详情页...")
            detailed_items = []
            
            for item in items:
                url = item.get('url', '')
                if url:
                    detail = await self.extract_detail_content(url)
                    item.update(detail)
                detailed_items.append(item)
            
            items = detailed_items
        
        # 保存结果
        output_file = self.save_results(items, mode)
        
        print(f"\n{'='*50}")
        print(f"提取完成: {len(items)} 条")
        print(f"保存至: {output_file}")
        print(f"{'='*50}")
        
        return items


def create_example_config():
    """创建示例配置文件"""
    example_config = {
        "name": "hackernews",
        "base_url": "https://news.ycombinator.com",
        "start_url": "https://news.ycombinator.com/",
        "data_dir": "data/hackernews",
        "concurrent_limit": 3,
        "headless": True,
        "selectors": {
            "item": ".athing",
            "title": ".titleline > a",
            "link": ".titleline > a",
            "score": ".score",
            "author": ".hnuser"
        },
        "fields": {
            "title": {"selector": ".titleline > a", "attribute": "text"},
            "url": {"selector": ".titleline > a", "attribute": "href"},
            "author": {"selector": ".hnuser", "attribute": "text"},
            "score": {"selector": ".score", "attribute": "text"}
        },
        "pagination": {
            "type": "link",
            "next_selector": ".morelink",
            "max_pages": 3
        },
        "detail_page": {
            "enabled": False
        }
    }
    
    config_path = Path("configs/hackernews.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(example_config, f, indent=2)
    
    print(f"✅ 示例配置已创建: {config_path}")
    return config_path


async def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("通用网页提取器 v1.0")
        print()
        print("用法:")
        print(f"  python3 {sys.argv[0]} <config.json> [mode]")
        print()
        print("参数:")
        print("  config.json  - 配置文件路径")
        print("  mode         - list(默认) 或 incremental")
        print()
        print("示例:")
        print(f"  python3 {sys.argv[0]} configs/moltbook.json")
        print(f"  python3 {sys.argv[0]} configs/hackernews.json incremental")
        print()
        print("创建示例配置:")
        print(f"  python3 {sys.argv[0]} --example")
        return
    
    if sys.argv[1] == "--example":
        create_example_config()
        return
    
    config_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "list"
    
    if not Path(config_path).exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return
    
    extractor = GenericExtractor(config_path)
    await extractor.run(mode=mode)


if __name__ == "__main__":
    asyncio.run(main())
