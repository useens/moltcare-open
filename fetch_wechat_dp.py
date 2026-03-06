from DrissionPage import ChromiumPage, ChromiumOptions

url = 'https://mp.weixin.qq.com/s/4XUQuGZcNb7d3Bhu_XEaUA'

try:
    # Use headless mode
    options = ChromiumOptions()
    options.headless(True)
    
    page = ChromiumPage(options)
    page.get(url)
    
    # Wait for content
    page.wait(5)
    
    # Get title
    title = page.title
    print(f'Title: {title}')
    
    # Try to get article content
    content_elem = page.ele('#js_content', timeout=3)
    if content_elem:
        content = content_elem.text
        print('\nContent:')
        print('='*50)
        print(content[:5000])
    else:
        # Fallback to body
        body = page.ele('tag:body')
        print('\nBody content:')
        print('='*50)
        print(body.text[:3000])
    
    page.quit()
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
