#!/usr/bin/env python3
"""测试 Playwright 访问 DuckDuckGo（调试模式）"""
from playwright.sync_api import sync_playwright
from urllib.parse import quote

def test_debug():
    """调试访问"""

    query = "test"
    max_results = 3
    results = []

    print(f"🔍 调试访问: {query}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                # 使用 DuckDuckGo HTML 模式
                search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
                print(f"   访问: {search_url}")

                page.goto(search_url, timeout=30000, wait_until='networkidle')
                page.wait_for_timeout(5000)

                # 获取页面内容
                page_title = page.title()
                print(f"   页面标题: {page_title}")

                # 获取整个页面的文本（前500字符）
                body_text = page.inner_text('body')
                print(f"   页面内容（前500字符）:")
                print(f"   {body_text[:500]}")

                # 检查是否是保护页面
                if 'privacy' in body_text.lower() or 'protection' in body_text.lower():
                    print(f"   ⚠️ 被重定向到保护页面")
                    return False

                # 查找结果元素
                selectors = [
                    '.result',  # DuckDuckGo HTML 版本
                    'div.result',  # 备用
                    'a.result__a',  # 直接找链接
                ]

                for selector in selectors:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"   使用选择器 '{selector}' 找到 {len(elements)} 个元素")
                        for el in elements[:max_results]:
                            try:
                                if selector == 'a.result__a':
                                    title = el.inner_text()
                                    url = el.get_attribute('href')
                                    results.append({
                                        "title": title,
                                        "url": url,
                                        "source": "playwright"
                                    })
                                    print(f"   📄 {title[:60]}...")
                            except:
                                pass

                print(f"✅ 调试完成: 找到 {len(results)} 条结果")

            except Exception as e:
                print(f"❌ 访问失败: {e}")
                import traceback
                traceback.print_exc()

            finally:
                browser.close()

    except Exception as e:
        print(f"❌ 异常: {e}")

    return len(results) > 0

if __name__ == "__main__":
    test_debug()
