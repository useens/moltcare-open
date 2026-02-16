#!/usr/bin/env python3
"""
DEBT-006 Playwright 内容获取脚本 - SPA 增强版
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
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        print(f"[{datetime.now().isoformat()}] 正在加载页面...")
        
        # 拦截控制台日志
        logs = []
        page.on("console", lambda msg: logs.append(f"{msg.type}: {msg.text}"))
        
        # 加载页面
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        
        # SPA 通常需要等待 JS 执行和 API 请求完成
        print(f"[{datetime.now().isoformat()}] 等待网络空闲...")
        page.wait_for_load_state('networkidle', timeout=30000)
        
        # 额外等待 API 数据加载
        print(f"[{datetime.now().isoformat()}] 等待内容渲染...")
        page.wait_for_timeout(8000)
        
        print(f"[{datetime.now().isoformat()}] 提取内容...")
        
        # 获取标题
        title = page.title()
        print(f"标题: {title}")
        
        # 拍摄截图用于调试
        screenshot_path = '/root/.openclaw/workspace/memory/debt-learning/DEBT-006-debug.png'
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"截图已保存: {screenshot_path}")
        
        # 尝试获取文章内容 - 多种选择器策略
        content_selectors = [
            'article',
            '[class*="post-"]',
            '[class*="Post"]',
            '[class*="content"]',
            '[class*="Content"]',
            'main',
            '#root',
            '#app',
            'body'
        ]
        
        text_content = ""
        html_content = ""
        used_selector = ""
        
        for selector in content_selectors:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    el = page.locator(selector).first
                    text_content = el.inner_text()
                    html_content = el.inner_html()
                    used_selector = selector
                    print(f"找到选择器: {selector} (长度: {len(text_content)})")
                    if len(text_content) > 500:
                        print(f"内容长度足够，使用此选择器")
                        break
            except Exception as e:
                continue
        
        if not text_content or len(text_content) < 100:
            print("警告: 内容可能未完全加载")
            # 尝试获取整个 body
            text_content = page.locator('body').inner_text()
            html_content = page.locator('body').inner_html()
            used_selector = "body (fallback)"
        
        # 获取页面源代码
        page_source = page.content()
        
        browser.close()
        
        result = {
            'url': url,
            'title': title,
            'used_selector': used_selector,
            'content_html': html_content,
            'page_source': page_source,
            'text': text_content,
            'console_logs': logs,
            'fetched_at': datetime.now().isoformat()
        }
        
        print(f"[{datetime.now().isoformat()}] 完成!")
        print(f"- 最终文本长度: {len(text_content)} 字符")
        
        return result

if __name__ == '__main__':
    try:
        result = fetch_moltbook()
        
        # 保存 JSON
        json_file = '/root/.openclaw/workspace/memory/debt-learning/DEBT-006-source.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            # 限制 JSON 大小
            json.dump({
                'url': result['url'],
                'title': result['title'],
                'used_selector': result['used_selector'],
                'text': result['text'][:20000],  # 限制文本长度
                'fetched_at': result['fetched_at']
            }, f, ensure_ascii=False, indent=2)
        print(f"\nJSON 已保存: {json_file}")
        
        # 保存纯文本
        txt_file = '/root/.openclaw/workspace/memory/debt-learning/DEBT-006-source.txt'
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"URL: {result['url']}\n")
            f.write(f"Title: {result['title']}\n")
            f.write(f"Selector: {result['used_selector']}\n")
            f.write(f"Fetched: {result['fetched_at']}\n")
            f.write(f"\n{'='*80}\n\n")
            f.write(result['text'])
        print(f"文本已保存: {txt_file}")
        
        # 保存 HTML 用于分析
        html_file = '/root/.openclaw/workspace/memory/debt-learning/DEBT-006-source.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(result['page_source'])
        print(f"HTML 已保存: {html_file}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
