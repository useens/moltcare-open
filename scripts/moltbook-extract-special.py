#!/usr/bin/env python3
"""
Moltbook 专用提取脚本 - 强化版
使用 Playwright 完整渲染 JavaScript
"""
import asyncio
import json
from playwright.async_api import async_playwright

CHROMIUM_PATH = '/usr/bin/chromium'
URL = "https://www.moltbook.com/post/cbd6474f"

async def extract_moltbook():
    """穷尽所有方法提取 Moltbook 内容"""
    results = {
        "url": URL,
        "attempts": [],
        "success": False,
        "content": None,
        "title": None
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=CHROMIUM_PATH,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        
        # 尝试 1: 标准桌面 UA
        try:
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            
            print("[尝试1] 标准桌面模式...")
            await page.goto(URL, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            
            # 等待内容加载
            try:
                await page.wait_for_selector('article, main, [class*="post"], [class*="content"]', timeout=10000)
            except:
                pass
            
            content = await page.locator('body').inner_text()
            title = await page.title()
            
            results["attempts"].append({
                "method": "desktop_standard",
                "title": title,
                "content_length": len(content),
                "content_preview": content[:500]
            })
            
            if len(content) > 1000 and "Loading" not in content:
                results["success"] = True
                results["content"] = content
                results["title"] = title
                results["method"] = "desktop_standard"
                await browser.close()
                return results
                
            await context.close()
        except Exception as e:
            results["attempts"].append({"method": "desktop_standard", "error": str(e)})
        
        # 尝试 2: 移动端 UA
        try:
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
                viewport={'width': 390, 'height': 844}
            )
            page = await context.new_page()
            
            print("[尝试2] 移动端模式...")
            await page.goto(URL, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            
            content = await page.locator('body').inner_text()
            title = await page.title()
            
            results["attempts"].append({
                "method": "mobile",
                "title": title,
                "content_length": len(content),
                "content_preview": content[:500]
            })
            
            if len(content) > 1000 and "Loading" not in content:
                results["success"] = True
                results["content"] = content
                results["title"] = title
                results["method"] = "mobile"
                await browser.close()
                return results
                
            await context.close()
        except Exception as e:
            results["attempts"].append({"method": "mobile", "error": str(e)})
        
        # 尝试 3: 长等待 + 滚动
        try:
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            
            print("[尝试3] 长等待+滚动模式...")
            await page.goto(URL, wait_until='load', timeout=60000)
            await page.wait_for_timeout(10000)
            
            # 滚动页面触发懒加载
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(3000)
            
            content = await page.locator('body').inner_text()
            title = await page.title()
            
            results["attempts"].append({
                "method": "long_wait_scroll",
                "title": title,
                "content_length": len(content),
                "content_preview": content[:500]
            })
            
            if len(content) > 1000 and "Loading" not in content:
                results["success"] = True
                results["content"] = content
                results["title"] = title
                results["method"] = "long_wait_scroll"
                await browser.close()
                return results
            
            # 尝试获取 HTML 源码
            html = await page.content()
            results["attempts"][-1]["html_length"] = len(html)
            
            await context.close()
        except Exception as e:
            results["attempts"].append({"method": "long_wait_scroll", "error": str(e)})
        
        # 尝试 4: API 端点检查
        try:
            context = await browser.new_context()
            page = await context.new_page()
            
            print("[尝试4] 监听 API 请求...")
            api_responses = []
            
            def handle_response(response):
                if 'api' in response.url or 'json' in response.url:
                    api_responses.append(response.url)
            
            page.on('response', handle_response)
            await page.goto(URL, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            
            results["attempts"].append({
                "method": "api_monitor",
                "api_urls": api_responses[:10]
            })
            
            await context.close()
        except Exception as e:
            results["attempts"].append({"method": "api_monitor", "error": str(e)})
        
        await browser.close()
    
    return results

if __name__ == '__main__':
    result = asyncio.run(extract_moltbook())
    print(json.dumps(result, ensure_ascii=False, indent=2))
