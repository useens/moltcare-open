import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

url = 'https://mp.weixin.qq.com/s/4XUQuGZcNb7d3Bhu_XEaUA'

options = uc.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

try:
    driver = uc.Chrome(options=options, version_main=120)
    driver.get(url)
    time.sleep(10)
    
    title = driver.title
    
    try:
        content_elem = driver.find_element(By.ID, 'js_content')
        content = content_elem.text
    except:
        content = driver.find_element(By.TAG_NAME, 'body').text
    
    try:
        author = driver.find_element(By.ID, 'js_name').text
    except:
        author = 'Unknown'
    
    print(f'Title: {title}')
    print(f'Author: {author}')
    print('\n' + '='*50)
    print('Content:')
    print('='*50)
    print(content[:5000])
    
    driver.quit()
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
