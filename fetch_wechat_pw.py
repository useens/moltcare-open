from playwright.sync_api import sync_playwright
import time

url = 'https://mp.weixin.qq.com/s/4XUQuGZcNb7d3Bhu_XEaUA'

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        page = browser.new_page()
        
        # Set user agent
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        page.goto(url, wait_until='networkidle', timeout=60000)
        time.sleep(5)
        
        # Get title
        title = page.title()
        print(f'Title: {title}')
        
        # Try to get content
        try:
            content_elem = page.query_selector('#js_content')
            if content_elem:
                content = content_elem.inner_text()
                print('\nContent:')
                print('='*50)
                print(content[:5000])
            else:
                # Get body text
                body = page.query_selector('body')
                if body:
                    print('\nBody content:')
                    print('='*50)
                    print(body.inner_text()[:3000])
        except Exception as e:
            print(f'Content error: {e}')
            # Get page source
            html = page.content()
            print('\nHTML preview:')
            print(html[:2000])
        
        browser.close()
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
