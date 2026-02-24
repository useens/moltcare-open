#!/usr/bin/env python3
"""
网页内容提取工具 - 简化版
直接访问URL提取结构化内容
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("错误: 请先安装playwright: pip install playwright")
    sys.exit(1)

async def extract_url(url: str, max_chars: int = 3000):
    """提取单个URL的结构化内容"""
    
    print(f"🔍 提取: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # 提取标题
            title = await page.title()
            print(f"✅ 标题: {title[:80]}")
            
            # 提取主要文本内容
            content = []
            
            # 标题 (h1-h3)
            for level in ["h1", "h2", "h3"]:
                elements = await page.query_selector_all(level)
                for el in elements[:5]:
                    text = await el.inner_text()
                    if text.strip():
                        content.append(f"[{level.upper()}] {text.strip()}")
            
            # 段落 (p)
            p_elements = await page.query_selector_all("p")
            total_len = 0
            for el in p_elements:
                text = await el.inner_text()
                if text.strip() and len(text.strip()) > 30:
                    content.append(text.strip())
                    total_len += len(text.strip())
                    if total_len > max_chars:
                        break
            
            result = {
                "url": url,
                "title": title,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            return {"url": url, "error": str(e)}
        finally:
            await browser.close()

def format_output(data: dict) -> str:
    """格式化输出"""
    if "error" in data:
        return f"# 提取失败\n**URL**: {data['url']}\n**错误**: {data['error']}\n"
    
    lines = [f"# {data['title']}", f"**URL**: {data['url']}", ""]
    
    for item in data['content'][:20]:  # 限制输出
        if item.startswith("["):
            lines.append(f"\n{item}")
        else:
            lines.append(f"{item}\n")
    
    return "\n".join(lines)

async def main():
    if len(sys.argv) < 2:
        print("用法: python web_extract_simple.py <URL>")
        print("示例: python web_extract_simple.py https://www.zhihu.com")
        sys.exit(1)
    
    url = sys.argv[1]
    data = await extract_url(url)
    
    output = format_output(data)
    print("\n" + "="*60)
    print(output)
    print("="*60)
    
    # 保存
    safe_url = url.replace("://", "_").replace("/", "_")[:30]
    output_file = f"/tmp/extract_{safe_url}_{datetime.now().strftime('%H%M%S')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"\n💾 已保存: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
