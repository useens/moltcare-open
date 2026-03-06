#!/usr/bin/env python3
"""
网络访问示例 - 使用共享环境的工具
"""

# 基础HTTP
import requests
import httpx

# 浏览器自动化
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except:
    HAS_PLAYWRIGHT = False

# 反爬绕过
try:
    import scrapling
    from scrapling import ScraplingFetcher
    HAS_SCRAPLING = True
except:
    HAS_SCRAPLING = False

def basic_fetch(url):
    """基础网页获取"""
    try:
        response = requests.get(url, timeout=30)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def browser_fetch(url):
    """浏览器获取"""
    if not HAS_PLAYWRIGHT:
        return "Playwright not available"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        return f"Error: {e}"

def stealth_fetch(url):
    """反爬绕过获取"""
    if not HAS_SCRAPLING:
        return "Scrapling not available"
    
    try:
        fetcher = ScraplingFetcher()
        return fetcher.get(url).text
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    
    print(f"Fetching: {url}")
    print("-" * 50)
    print("Basic fetch:")
    print(basic_fetch(url)[:500])
    print("\nBrowser fetch:")
    print(browser_fetch(url)[:500])
