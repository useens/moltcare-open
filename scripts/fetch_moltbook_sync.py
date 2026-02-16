from playwright.sync_api import sync_playwright
import json
from datetime import datetime

def fetch_moltbook():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        print(f"[{datetime.now()}] 正在加载页面...")
        
        # 导航到页面
        response = page.goto(
            'https://www.moltbook.com/post/cbd6474f', 
            wait_until='domcontentloaded',
            timeout=60000
        )
        print(f"页面状态: {response.status if response else 'N/A'}")
        
        # 等待网络空闲
        page.wait_for_load_state('networkidle', timeout=60000)
        print(f"[{datetime.now()}] 网络空闲，等待渲染...")
        
        # 等待更长时间让 JavaScript 渲染
        page.wait_for_timeout(8000)
        
        # 获取页面标题
        title = page.title()
        print(f"\n页面标题: {title}")
        
        # 检查内容是否加载
        content_html = page.content()
        print(f"页面 HTML 长度: {len(content_html)}")
        
        # 尝试找到文章内容
        selectors_to_try = [
            'article',
            'main article',
            '[class*="post"]',
            '[class*="content"]',
            'main'
        ]
        
        article_text = None
        for selector in selectors_to_try:
            try:
                elements = page.locator(selector)
                count = elements.count()
                if count > 0:
                    text = elements.first.inner_text()
                    if text and len(text) > 200:  # 如果内容足够长
                        article_text = text
                        print(f"✓ 使用选择器 '{selector}' 提取内容: {len(text)} 字符")
                        break
            except Exception as e:
                continue
        
        # 如果找不到特定内容，获取 body 文本
        if not article_text:
            article_text = page.locator('body').inner_text()
            print(f"✓ 使用 body 提取内容: {len(article_text)} 字符")
        
        # 尝试获取更多结构化信息
        try:
            # 查找标题
            h1_text = page.locator('h1').first.inner_text()
        except:
            h1_text = title
            
        browser.close()
        
        return {
            'title': title,
            'h1': h1_text,
            'url': 'https://www.moltbook.com/post/cbd6474f',
            'timestamp': datetime.now().isoformat(),
            'content_text': article_text,
            'content_length': len(article_text)
        }

if __name__ == '__main__':
    print("="*60)
    print("Moltbook 内容抓取工具")
    print("="*60)
    
    try:
        result = fetch_moltbook()
        
        # 保存结果
        output_file = '/root/.openclaw/workspace/moltbook_cbd6474f_raw.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ 内容已保存到: {output_file}")
        print(f"✓ 内容长度: {result['content_length']} 字符")
        print(f"{'='*60}")
        
        # 显示内容预览
        print("\n--- 内容预览 (前2500字符) ---")
        print(result['content_text'][:2500])
        print("\n... [内容已截断，完整内容已保存]")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
