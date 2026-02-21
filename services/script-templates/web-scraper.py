#!/usr/bin/env python3
"""
智能网页抓取器 - 自动化数据采集
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

class WebScraper:
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.data = []
    
    def fetch_page(self, url: str) -> BeautifulSoup:
        """获取页面内容"""
        time.sleep(self.delay)  # 礼貌延迟
        
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    
    def extract_data(self, soup: BeautifulSoup, selectors: dict) -> dict:
        """根据选择器提取数据"""
        result = {}
        for key, selector in selectors.items():
            element = soup.select_one(selector)
            result[key] = element.text.strip() if element else None
        return result
    
    def scrape_list(self, list_url: str, item_selector: str, 
                   data_selectors: dict, next_page_selector: str = None) -> list:
        """抓取列表页"""
        current_url = list_url
        
        while current_url:
            print(f"正在抓取: {current_url}")
            soup = self.fetch_page(current_url)
            
            # 提取列表项
            items = soup.select(item_selector)
            for item in items:
                data = self.extract_data(item, data_selectors)
                self.data.append(data)
            
            # 检查是否有下一页
            if next_page_selector:
                next_link = soup.select_one(next_page_selector)
                if next_link and next_link.get('href'):
                    current_url = urljoin(current_url, next_link['href'])
                else:
                    current_url = None
            else:
                current_url = None
        
        return self.data
    
    def save_data(self, filename: str):
        """保存数据"""
        output_path = Path(filename)
        
        if output_path.suffix == '.json':
            with open(output_path, 'w') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        elif output_path.suffix == '.csv':
            import pandas as pd
            df = pd.DataFrame(self.data)
            df.to_csv(output_path, index=False)
        
        print(f"✅ 数据已保存: {output_path} (共 {len(self.data)} 条)")

if __name__ == "__main__":
    scraper = WebScraper(delay=1.5)
    
    # 使用示例
    print("""
使用示例:
    scraper = WebScraper(delay=2)
    data = scraper.scrape_list(
        list_url="https://example.com/items",
        item_selector=".item",
        data_selectors={
            "title": ".title",
            "price": ".price",
            "link": "a"
        },
        next_page_selector=".next-page"
    )
    scraper.save_data("output.json")
    """)
