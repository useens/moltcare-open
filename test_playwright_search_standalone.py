#!/usr/bin/env python3
"""测试 Playwright 搜索（独立版本）"""
from playwright.sync_api import sync_playwright
from urllib.parse import quote

def test_playwright_search():
    """测试 Playwright 搜索"""

    query = "agent memory systems"
    max_results = 3
    results = []

    print(f"🔍 使用 Playwright + Chromium 搜索: {query}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()

            try:
                # 使用 DuckDuckGo HTML 模式（不需要 JS，更容易提取）
                search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
                print(f"   访问: {search_url}")

                page.goto(search_url, timeout=30000)
                page.wait_for_timeout(3000)

                # 获取页面内容检查
                page_title = page.title()
                print(f"   页面标题: {page_title}")

                # DuckDuckGo HTML 版本的结果在 .result 类中
                result_elements = page.query_selector_all('.result')
                print(f"   找到 {len(result_elements)} 个结果元素")

                for i, element in enumerate(result_elements[:max_results], 1):
                    try:
                        # 提取标题和链接
                        link = element.query_selector('a.result__a')
                        if not link:
                            continue

                        title = link.inner_text()
                        url = link.get_attribute('href')

                        # 提取描述
                        snippet_el = element.query_selector('.result__snippet')
                        snippet = ""
                        if snippet_el:
                            snippet_text = snippet_el.inner_text()
                            if snippet_text:
                                snippet = snippet_text

                        if title and url:
                            results.append({
                                "title": title.strip()[:100],
                                "url": url.strip(),
                                "snippet": snippet.strip()[:300] if snippet else "",
                                "source": "playwright_duckduckgo"
                            })
                            print(f"  📄 [{i}] {title[:60]}...")

                    except Exception as e:
                        print(f"  ⚠️ 解析结果 #{i} 失败: {e}")
                        continue

                print(f"✅ 搜索完成: 找到 {len(results)} 条结果")

            except Exception as e:
                print(f"❌ DuckDuckGo 搜索失败: {e}")

            finally:
                browser.close()

    except ImportError:
        print("❌ Playwright 未安装")
        return False
    except Exception as e:
        print(f"❌ Playwright 搜索异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n📊 结果统计: {len(results)} 条")

    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   来源: {result['source']}")
        print(f"   摘要: {result['snippet'][:100] if result.get('snippet') else 'N/A'}...")

    return len(results) > 0

if __name__ == "__main__":
    success = test_playwright_search()
    print(f"\n{'✅ 测试成功' if success else '❌ 测试失败'}")
