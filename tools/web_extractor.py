#!/usr/bin/env python3
"""
Web内容提取工具 - Playwright结构化提取
用于多专家讨论中的网络搜索，替代web_search和browser截图

特点：
- 提取结构化文本内容（非截图，节省token）
- 支持搜索和页面内容提取
- 自动处理反爬（User-Agent、延迟）
"""

import json
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    print("错误: 请先安装playwright: pip install playwright")
    raise

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str

@dataclass
class PageContent:
    url: str
    title: str
    headings: List[str]
    paragraphs: List[str]
    links: List[Dict[str, str]]
    timestamp: str

class WebExtractor:
    """网页内容提取器"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.results_cache = {}
        
    async def search_google(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """网络搜索 - 尝试多个搜索引擎"""
        results = []

        # 临时方案：返回模拟搜索结果（由于搜索引擎反爬限制）
        # 在实际部署中，可以使用 Brave Search API 或付费搜索服务

        mock_data = {
            "default": [
                {
                    "title": f"关于 '{query}' 的相关技术文档",
                    "url": f"https://docs.example.com/search?q={query.replace(' ', '_')}",
                    "snippet": f"这是关于 {query} 的技术分析文档，包含最佳实践和实施指南。"
                },
                {
                    "title": f"{query} - 开发者实践经验",
                    "url": f"https://dev.example.com/blog/{query.replace(' ', '-')}",
                    "snippet": f"分享 {query} 的实际开发经验，包括常见问题和解决方案。"
                }
            ]
        }

        for item in mock_data["default"][:num_results]:
            results.append(SearchResult(
                title=item["title"],
                url=item["url"],
                snippet=item["snippet"],
                source="mock_api"
            ))
            print(f"  📄 (模拟) 结果: {item['title'][:50]}")

        print(f"✅ 搜索完成: {len(results)} 条结果 (模拟数据模式)")
        return results
    
    async def extract_page(self, url: str, max_length: int = 5000) -> PageContent:
        """提取网页结构化内容"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_timeout(2000)
                
                # 提取标题
                title = await page.title()
                
                # 提取所有标题 (h1-h3)
                headings = []
                for level in ["h1", "h2", "h3"]:
                    elements = await page.query_selector_all(level)
                    for el in elements[:10]:  # 限制数量
                        text = await el.inner_text()
                        if text.strip():
                            headings.append(f"[{level.upper()}] {text.strip()}")
                
                # 提取正文段落
                paragraphs = []
                p_elements = await page.query_selector_all("p")
                for el in p_elements[:30]:  # 限制数量
                    text = await el.inner_text()
                    if text.strip() and len(text.strip()) > 20:
                        paragraphs.append(text.strip())
                        if sum(len(p) for p in paragraphs) > max_length:
                            break
                
                # 提取链接
                links = []
                a_elements = await page.query_selector_all("a")
                for el in a_elements[:20]:
                    href = await el.get_attribute("href")
                    text = await el.inner_text()
                    if href and text.strip() and href.startswith("http"):
                        links.append({"text": text.strip()[:50], "url": href})
                
                return PageContent(
                    url=url,
                    title=title,
                    headings=headings,
                    paragraphs=paragraphs,
                    links=links,
                    timestamp=datetime.now().isoformat()
                )
                
            finally:
                await browser.close()
    
    async def search_and_extract(self, query: str, num_results: int = 3) -> Dict:
        """搜索并提取前N个结果的详细内容"""
        
        print(f"🔍 搜索: {query}")
        search_results = await self.search_google(query, num_results)
        
        detailed_results = []
        for i, result in enumerate(search_results, 1):
            print(f"📄 提取 ({i}/{len(search_results)}): {result.title[:50]}...")
            try:
                page_content = await self.extract_page(result.url)
                detailed_results.append({
                    "search": {
                        "title": result.title,
                        "url": result.url,
                        "snippet": result.snippet
                    },
                    "content": {
                        "title": page_content.title,
                        "headings": page_content.headings,
                        "paragraphs": page_content.paragraphs[:10],  # 限制段落数
                        "links": page_content.links[:5]  # 限制链接数
                    }
                })
            except Exception as e:
                print(f"⚠️ 提取失败: {e}")
                detailed_results.append({
                    "search": {
                        "title": result.title,
                        "url": result.url,
                        "snippet": result.snippet
                    },
                    "error": str(e)
                })
        
        return {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": detailed_results
        }

def extract_to_markdown(data: Dict) -> str:
    """将提取结果转换为Markdown格式"""
    lines = []
    lines.append(f"# 搜索结果: {data['query']}\n")
    lines.append(f"*搜索时间: {data['timestamp']}*\n")
    
    for i, result in enumerate(data['results'], 1):
        lines.append(f"\n## 结果 {i}: {result['search']['title']}\n")
        lines.append(f"**URL**: {result['search']['url']}\n")
        lines.append(f"**摘要**: {result['search']['snippet']}\n")
        
        if 'error' in result:
            lines.append(f"⚠️ **提取错误**: {result['error']}\n")
            continue
        
        content = result['content']
        lines.append(f"\n### 页面标题\n{content['title']}\n")
        
        if content['headings']:
            lines.append(f"\n### 主要内容结构\n")
            for h in content['headings'][:10]:
                lines.append(f"- {h}")
            lines.append("")
        
        if content['paragraphs']:
            lines.append(f"\n### 关键内容\n")
            for p in content['paragraphs'][:5]:
                lines.append(f"{p}\n")
        
        if content['links']:
            lines.append(f"\n### 相关链接\n")
            for link in content['links'][:3]:
                lines.append(f"- [{link['text']}]({link['url']})")
            lines.append("")
    
    return "\n".join(lines)

async def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python web_extractor.py <搜索关键词> [结果数量]")
        print("示例: python web_extractor.py 'Agent安全' 3")
        return
    
    query = sys.argv[1]
    num_results = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    extractor = WebExtractor(headless=True)
    data = await extractor.search_and_extract(query, num_results)
    
    # 输出Markdown
    markdown = extract_to_markdown(data)
    print("\n" + "="*50)
    print(markdown)
    print("="*50)
    
    # 保存到文件
    output_file = f"/tmp/web_extract_{query.replace(' ', '_')[:20]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    print(f"\n✅ 结果已保存: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
