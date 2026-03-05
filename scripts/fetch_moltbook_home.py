from playwright.sync_api import sync_playwright
import json
from datetime import datetime

def fetch_moltbook_home():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        print(f"[{datetime.now()}] 正在加载 moltbook 主页...")
        
        page.goto('https://www.moltbook.com/', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        
        title = page.title()
        print(f"页面标题: {title}")
        
        # 获取所有可见内容
        body_text = page.locator('body').inner_text()
        
        browser.close()
        
        return {
            'title': title,
            'timestamp': datetime.now().isoformat(),
            'content': body_text
        }

if __name__ == '__main__':
    result = fetch_moltbook_home()
    print(f"\n内容长度: {len(result['content'])} 字符")
    print("\n--- 内容预览 ---")
    print(result['content'][:3000])
