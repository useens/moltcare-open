#!/usr/bin/env python3
"""测试 Playwright 访问静态文档"""
from playwright.sync_api import sync_playwright

def test_static_docs():
    """测试访问静态技术文档"""

    query = "python"
    max_results = 2

    # 预定义技术资源库
    tech_resources = {
        "python": [
            ("https://docs.python.org/3/", "Python 3 官方文档"),
            ("https://docs.python.org/3/library/", "Python 标准库"),
        ],
    }

    query_lower = query.lower()
    matched_urls = []

    for keyword, urls in tech_resources.items():
        if keyword in query_lower:
            matched_urls.extend(urls)

    print(f"🔍 匹配到 {len(matched_urls)} 个相关文档")

    # 提取内容
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={'width': 1280, 'height': 800}
        )

        for i, (url, description) in enumerate(matched_urls[:max_results], 1):
            page = context.new_page()

            try:
                print(f"   访问 [{i}]: {url}")

                page.goto(url, timeout=30000, wait_until='networkidle')
                page.wait_for_timeout(3000)

                # 获取页面内容
                page_title = page.title()
                print(f"   标题: {page_title}")

                # 获取一些段落
                p_elements = page.query_selector_all("p, h1, h2")
                snippet_parts = []
                for el in p_elements[:3]:
                    text = str(el.inner_text()).strip()
                    if text and len(text) > 20:
                        snippet_parts.append(text)
                snippet = " ".join(snippet_parts) if snippet_parts else ""

                print(f"   摘要: {snippet[:200]}...")

                print(f"  ✅ 成功")

            except Exception as e:
                print(f"  ❌ 失败: {e}")
            finally:
                page.close()

        browser.close()

    print("\n✅ 测试完成")

if __name__ == "__main__":
    test_static_docs()
