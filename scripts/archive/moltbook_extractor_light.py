#!/usr/bin/env python3
"""
Moltbook 数据提取器 v1.0 - 轻量化版本
使用 requests + BeautifulSoup，无需 Playwright
"""

import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

def extract_moltbook_data(username="LinLin_v1"):
    """提取 Moltbook 用户主页数据"""
    url = f"https://www.moltbook.com/u/{username}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 提取脚本中的 JSON 数据（Next.js 通常内嵌数据）
        scripts = soup.find_all('script')
        data = {
            "username": username,
            "url": url,
            "extracted_at": datetime.now().isoformat(),
            "posts": [],
            "raw_html_size": len(resp.text)
        }
        
        # 尝试从 __NEXT_DATA__ 提取
        for script in scripts:
            if script.string and '__NEXT_DATA__' in script.string:
                try:
                    json_match = re.search(r'window\.__NEXT_DATA__\s*=\s*({.+?});', script.string, re.DOTALL)
                    if json_match:
                        next_data = json.loads(json_match.group(1))
                        # 这里可以进一步解析 next_data 结构
                        data['has_next_data'] = True
                        data['next_data_keys'] = list(next_data.keys())[:5]
                except:
                    pass
        
        # 从 HTML 直接提取帖子信息（备用方案）
        # 查找包含帖子信息的元素
        post_links = soup.find_all('a', href=re.compile(r'/p/'))
        for link in post_links[:10]:
            title_elem = link.find(['h2', 'h3', 'h4', 'span', 'div'], class_=re.compile(r'title|heading', re.I))
            if title_elem:
                data['posts'].append({
                    "title": title_elem.get_text(strip=True)[:100],
                    "href": link.get('href', '')
                })
        
        # 提取 karma 等信息
        karma_elem = soup.find(string=re.compile(r'karma|Karma'))
        if karma_elem:
            data['karma_text'] = karma_elem.strip()[:50]
        
        return data
        
    except Exception as e:
        return {
            "error": str(e),
            "username": username,
            "extracted_at": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "LinLin_v1"
    
    result = extract_moltbook_data(username)
    print(json.dumps(result, indent=2, ensure_ascii=False))
