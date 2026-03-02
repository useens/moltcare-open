#!/usr/bin/env python3
"""
Web 内容提取工具 - Playwright 纯提取模式
用于多专家讨论中的网页内容提取

特点：
- 提取结构化文本内容（非截图，节省token）
- 只做网页内容提取，不做搜索
- 使用 Playwright + Chromium 真实访问网页
"""

import asyncio
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    print("错误: 请先安装playwright: pip install playwright")
    raise

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

    async def extract_page(self, url: str, max_length: int = 10000) -> PageContent:
        """提取网页结构化内容"""

        print(f"🔍 提取网页内容: {url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(5000)  # 更长的等待时间，等待 JS 渲染

                # 提取页面标题
                title = await page.title()

                # 获取整个页面的 HTML 文本，检查内容
                body_text = await page.inner_text('body')
                print(f"   页面总字符数: {len(body_text)}")

                # 提取所有标题 (h1-h6)
                headings = []
                for level in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    elements = await page.query_selector_all(level)
                    for el in elements[:20]:  # 限制数量
                        text = await el.inner_text()
                        if text.strip() and len(text.strip()) < 200:
                            headings.append(f"[{level.upper()}] {text.strip()}")

                # 提取正文段落 - 尝试更多选择器
                paragraphs = []
                selectors = [
                    "p",  # 通用
                    "div[class*='content'] p",  # content div
                    "article p",  # article 标签
                    "main p",  # main 标签
                    "[data-content] p",  # data attribute
                    ".prose p",  # prose class
                    "div[class*='post'] p",  # post div
                ]

                for selector in selectors:
                    if len(paragraphs) >= 20:  # 已经找到了足够多的段落
                        break
                    try:
                        p_elements = await page.query_selector_all(selector)
                        for el in p_elements:
                            text = await el.inner_text()
                            text = text.strip()
                            # 过滤：长度合理，不是导航文本
                            if text and len(text) > 30 and len(text) < 1000:
                                # 排除一些常见的无关文本
                                skip_keywords = ['cookie', 'privacy', 'terms', 'subscribe', 'login', 'sign up', 'skip to', '©']
                                if not any(kw in text.lower() for kw in skip_keywords):
                                    # 去重
                                    if text not in paragraphs:
                                        paragraphs.append(text)
                                        if sum(len(p) for p in paragraphs) > max_length:
                                            break
                        if paragraphs:
                            print(f"   使用选择器 '{selector}' 找到 {len(paragraphs)} 段落")
                    except:
                        continue

                # 如果还是找不到，尝试获取所有文本块
                if len(paragraphs) < 5:
                    print(f"   ⚠️ 段落较少，使用降级方案...")
                    # 获取所有 div 文本
                    divs = await page.query_selector_all("div")
                    for div in divs[:50]:
                        text = await div.inner_text()
                        text = text.strip()
                        if text and len(text) > 100 and len(text) < 5000:
                            # 跳过太短或太长的文本
                            skip_keywords = ['menu', 'nav', 'header', 'footer', 'sidebar', '©']
                            if not any(kw in text.lower() for kw in skip_keywords):
                                paragraphs.append(text)
                                if len(paragraphs) >= 20:
                                    break

                # 提取链接
                links = []
                a_elements = await page.query_selector_all("a[href]")
                seen_urls = set()
                for el in a_elements:
                    href = await el.get_attribute('href')
                    text = await el.inner_text()
                    if href and href.startswith('http') and text.strip():
                        # 去重
                        if href not in seen_urls and len(text.strip()) < 100:
                            links.append({"text": text.strip()[:80], "url": href})
                            seen_urls.add(href)
                            if len(links) >= 20:
                                break

                print(f"✅ 提取完成: {len(paragraphs)} 段, {len(headings)} 标题, {len(links)} 链接")

                return PageContent(
                    url=url,
                    title=title,
                    headings=headings,
                    paragraphs=paragraphs,
                    links=links,
                    timestamp=datetime.now().isoformat()
                )

            except Exception as e:
                print(f"❌ 提取失败: {e}")
                raise

            finally:
                await browser.close()

def extract_to_markdown(content: PageContent) -> str:
    """将提取结果转换为Markdown格式"""
    lines = []
    lines.append(f"# 提取内容: {content.title}\n")
    lines.append(f"**URL**: {content.url}\n")
    lines.append(f"**提取时间**: {content.timestamp}\n")

    if content.headings:
        lines.append(f"\n## 📋 内容结构\n")
        for h in content.headings[:20]:
            lines.append(f"{h}\n")

    if content.paragraphs:
        lines.append(f"\n## 📄 主要内容\n")
        for p in content.paragraphs[:30]:
            lines.append(f"{p}\n")

    if content.links:
        lines.append(f"\n## 🔗 相关链接\n")
        for link in content.links[:10]:
            lines.append(f"- [{link['text']}]({link['url']})")
        lines.append("")

    return "\n".join(lines)

async def main():
    """命令行入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python web_extractor.py <URL>")
        print("示例: python web_extractor.py 'https://example.com/article'")
        return

    url = sys.argv[1]

    extractor = WebExtractor(headless=True)
    content = await extractor.extract_page(url)

    # 输出Markdown
    markdown = extract_to_markdown(content)
    print("\n" + "="*60)
    print(markdown)
    print("="*60)

    # 保存到文件
    output_dir = Path("/root/.openclaw/workspace/data/web-extracts")
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = url.replace('https://', '').replace('http://', '').replace('/', '_')[:50]
    output_file = output_dir / f"{safe_filename}.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"\n✅ 结果已保存: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
