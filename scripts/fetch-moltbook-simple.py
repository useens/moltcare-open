#!/usr/bin/env python3
"""
DEBT-006 Playwright 内容获取脚本 - 同步版本
获取 Moltbook 原文: The Good Samaritan - m0ther
"""

from playwright.sync_api import sync_playwright
import json
from datetime import datetime

def fetch_moltbook():
    url = 'https://www.moltbook.com/post/94fc8fda'
    
    print(f"[{datetime.now().isoformat()}] 开始获取内容...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        print(f"[{datetime.now().isoformat()}] 正在加载页面...")
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        
        # 等待 JavaScript 渲染
        page.wait_for_timeout(5000)
        
        print(f"[{datetime.now().isoformat()}] 提取内容...")
        
        # 获取标题
        title = page.title()
        
        # 尝试获取文章内容 - 查找常见的内容容器
        content_selectors = [
            'article',
            '[class*="post"]',
            '[class*="content"]',
            'main',
            '#content',
            '.content',
            'body'
        ]
        
        text_content = ""
        html_content = ""
        
        for selector in content_selectors:
            try:
                if page.locator(selector).count() > 0:
                    text_content = page.locator(selector).first.inner_text()
                    html_content = page.locator(selector).first.inner_html()
                    print(f"[{datetime.now().isoformat()}] 使用选择器: {selector}")
                    break
            except Exception as e:
                continue
        
        if not text_content:
            text_content = page.locator('body').inner_text()
            html_content = page.locator('body').inner_html()
        
        browser.close()
        
        result = {
            'url': url,
            'title': title,
            'content_html': html_content,
            'text': text_content,
            'fetched_at': datetime.now().isoformat()
        }
        
        print(f"[{datetime.now().isoformat()}] 完成!")
        print(f"- 标题: {title}")
        print(f"- 文本长度: {len(text_content)} 字符")
        
        return result

if __name__ == '__main__':
    try:
        result = fetch_moltbook()
        
        # 保存 JSON
        json_file = '/root/.openclaw/workspace/memory/debt-learning/DEBT-006-source.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nJSON 已保存: {json_file}")
        
        # 保存纯文本
        txt_file = '/root/.openclaw/workspace/memory/debt-learning/DEBT-006-source.txt'
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"URL: {result['url']}\n")
            f.write(f"Title: {result['title']}\n")
            f.write(f"Fetched: {result['fetched_at']}\n")
            f.write(f"\n{'='*80}\n\n")
            f.write(result['text'])
        print(f"文本已保存: {txt_file}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
