#!/usr/bin/env python3
"""
使用Playwright绕过微信反爬，抓取公众号文章内容
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ 需要安装playwright: pip install playwright")
    print("   然后运行: playwright install chromium")
    sys.exit(1)


async def fetch_wechat_article(url: str) -> str:
    """抓取微信文章内容"""
    async with async_playwright() as p:
        # 使用系统代理（如果有的话）
        proxy = None
        # 如果需要设置代理，取消下面注释
        # proxy = {"server": "http://127.0.0.1:8080"}

        # 启动chromium，使用无头模式但更像真人
        browser = await p.chromium.launch(
            headless=True,
            slow_mo=200,  # 每个操作延迟200ms，更像真人
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--start-maximized',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            ]
        )

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            proxy=proxy,
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
        )

        page = await context.new_page()

        # 添加stealth插件效果 - 模拟真实浏览器
        await page.add_init_script("""
            // 覆盖navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // 模拟插件
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3],
                enumerable: true
            });

            // 模拟语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
                enumerable: true
            });

            // 创建假window.chrome对象
            window.chrome = {
                runtime: {},
                loadTimes: () => ({}),
                csi: () => ({}),
                app: {}
            };

            // 模拟屏幕信息
            Object.defineProperty(screen, 'width', { value: 1920 });
            Object.defineProperty(screen, 'height', { value: 1080 });
            Object.defineProperty(screen, 'colorDepth', { value: 24 });
        """)

        try:
            print(f"🔍 正在访问: {url}")
            response = await page.goto(url, wait_until='networkidle', timeout=30000)

            if response.status != 200:
                print(f"❌ HTTP状态码: {response.status}")
                return ""

            # 等待页面加载
            await page.wait_for_timeout(2000)

            # 微信文章通常在id="js_content"的div中
            content_selector = '#js_content'

            # 检查元素是否存在
            if await page.locator(content_selector).count() > 0:
                content_element = page.locator(content_selector).first
                # 获取innerHTML或innerText
                content = await content_element.inner_text()
                print(f"✅ 成功提取文章内容 ({len(content)} 字符)")
                return content
            else:
                # 尝试其他选择器
                selectors = [
                    '.rich_media_content',
                    'div.rich_media_area',
                    'div#js_editor_content'
                ]

                for sel in selectors:
                    if await page.locator(sel).count() > 0:
                        content = await page.locator(sel).first.inner_text()
                        print(f"✅ 使用备用选择器 {sel} 提取成功 ({len(content)} 字符)")
                        return content

                print("❌ 未找到文章内容元素")
                # 保存页面源码用于调试
                html = await page.content()
                debug_file = Path(f"/root/.openclaw/workspace/reports/wechat_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
                debug_file.write_text(html, encoding='utf-8')
                print(f"  已保存调试页面: {debug_file}")
                return ""

        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            return ""
        finally:
            await browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 fetch_wechat_article.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    content = asyncio.run(fetch_wechat_article(url))

    if content:
        print("\n" + "="*60)
        print("📄 文章内容:")
        print("="*60)
        print(content[:5000])  # 限制输出长度
        if len(content) > 5000:
            print(f"... (还有 {len(content)-5000} 字符)")

        # 保存到文件
        output_file = Path(f"/root/.openclaw/workspace/reports/wechat_article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        output_file.write_text(content, encoding='utf-8')
        print(f"\n💾 完整内容已保存到: {output_file}")
    else:
        print("❌ 未能提取内容")
