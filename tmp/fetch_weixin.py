#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import sys

url = "https://mp.weixin.qq.com/s/byZxYjvPUyGYpL5ZHUj0Xg"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

session = requests.Session()
session.headers.update(headers)

response = session.get(url, timeout=30, allow_redirects=True)
print(f"Status: {response.status_code}")
print(f"Final URL: {response.url}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print("\n" + "="*80 + "\n")

if 'captcha' in response.url.lower() or 'wappoc' in response.url.lower():
    print("⚠️ 被验证码拦截，无法直接获取")
    sys.exit(1)

# 尝试提取主要内容
soup = BeautifulSoup(response.text, 'html.parser')
title = soup.find('meta', property='og:title')
if title:
    print(f"标题: {title.get('content', 'N/A')}\n")

# 提取文章正文
article = soup.find(id='js_content')
if article:
    print(article.get_text('\n', strip=True))
else:
    # 尝试其他选择器
    body = soup.find('body')
    if body:
        print(body.get_text('\n', strip=True)[:5000])
