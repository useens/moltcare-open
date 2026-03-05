import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def fetch_moltbook():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        print(f"[{datetime.now()}] 正在加载页面...")
        
        # 设置更长的超时
        page.set_default_timeout(60000)
        
        # 导航到页面并等待网络空闲
        response = await page.goto(
            'https://www.moltbook.com/post/cbd6474f', 
            wait_until='networkidle',
            timeout=60000
        )
        print(f"页面状态: {response.status if response else 'N/A'}")
        
        # 等待更长时间让 JavaScript 渲染完成
        print(f"[{datetime.now()}] 等待 JavaScript 渲染...")
        await asyncio.sleep(5)
        
        # 等待内容出现 - 尝试多种可能的 CSS 选择器
        content_selectors = [
            'article',
            '[class*="post-content"]',
            '[class*="content"]',
            '.prose',
            '.rich_media_content',
            '#js_content',
            'main',
            'h1'
        ]
        
        found_selector = None
        for selector in content_selectors:
            try:
                # 等待元素出现
                await page.wait_for_selector(selector, timeout=10000)
                element = page.locator(selector).first
                if await element.is_visible():
                    count = await page.locator(selector).count()
                    print(f"✓ 找到选择器: {selector} (数量: {count})")
                    found_selector = selector
                    if selector in ['article', '[class*="post-content"]', '.prose']:
                        break
            except Exception as e:
                print(f"  未找到: {selector}")
                continue
        
        # 额外等待确保内容完全加载
        await asyncio.sleep(3)
        
        # 获取页面标题
        title = await page.title()
        print(f"\n页面标题: {title}")
        
        # 尝试多种方式提取内容
        content_data = {}
        
        # 方法1: 尝试获取文章正文
        try:
            article = await page.locator('article').first.inner_text()
            content_data['article'] = article[:5000] if len(article) > 5000 else article
            print(f"✓ 提取到 article 内容: {len(article)} 字符")
        except Exception as e:
            print(f"  无法提取 article: {e}")
        
        # 方法2: 获取 body 文本
        body_text = await page.locator('body').inner_text()
        content_data['body'] = body_text
        print(f"✓ 提取到 body 内容: {len(body_text)} 字符")
        
        # 方法3: 获取所有可见文本
        try:
            all_text = await page.evaluate('''() => {
                return document.body.innerText;
            }''')
            content_data['full_text'] = all_text
            print(f"✓ 提取到完整文本: {len(all_text)} 字符")
        except Exception as e:
            print(f"  无法提取完整文本: {e}")
        
        # 方法4: 获取页面 HTML 用于调试
        try:
            html_content = await page.content()
            content_data['html'] = html_content[:10000]  # 只保存前10000字符
        except Exception as e:
            print(f"  无法提取 HTML: {e}")
        
        await browser.close()
        
        return {
            'title': title,
            'url': 'https://www.moltbook.com/post/cbd6474f',
            'timestamp': datetime.now().isoformat(),
            'found_selector': found_selector,
            'content': content_data
        }

if __name__ == '__main__':
    try:
        result = asyncio.run(fetch_moltbook())
        
        # 保存结果
        output_file = '/root/.openclaw/workspace/moltbook_cbd6474f_raw.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ 内容已保存到: {output_file}")
        print(f"{'='*60}")
        
        # 显示内容预览
        if 'full_text' in result['content']:
            print("\n--- 内容预览 (前3000字符) ---")
            print(result['content']['full_text'][:3000])
            print("\n... [内容已截断]")
        elif 'body' in result['content']:
            print("\n--- 内容预览 (前3000字符) ---")
            print(result['content']['body'][:3000])
            print("\n... [内容已截断]")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
