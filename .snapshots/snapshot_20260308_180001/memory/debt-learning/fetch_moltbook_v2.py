#!/usr/bin/env python3
"""
Playwright 脚本 - 获取 Moltbook 文章原文
目标: https://www.moltbook.com/post/4b64728c
"""

import asyncio
from playwright.async_api import async_playwright

async def fetch_moltbook():
    """使用 Playwright 获取 Moltbook 文章全文"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        print("🌐 正在访问页面...")
        try:
            response = await page.goto('https://www.moltbook.com/post/4b64728c', 
                           wait_until='domcontentloaded', timeout=60000)
            print(f"✓ 页面加载完成，状态: {response.status if response else 'N/A'}")
        except Exception as e:
            print(f"⚠️ 页面加载超时或失败: {e}")
        
        # 等待内容加载
        print("⏳ 等待内容加载...")
        await page.wait_for_timeout(5000)
        
        # 获取页面所有文本内容
        print("📝 提取内容...")
        content_text = await page.locator('body').inner_text()
        
        # 获取页面标题
        try:
            title = await page.title()
        except:
            title = "无标题"
        
        await browser.close()
        
        return {
            'title': title,
            'text': content_text
        }

def main():
    """保存获取的内容到文件"""
    result = asyncio.run(fetch_moltbook())
    
    print(f"\n📄 标题: {result['title']}")
    print(f"📝 内容长度: {len(result['text'])} 字符")
    
    # 保存文本内容
    output_path = '/root/.openclaw/workspace/memory/debt-learning/DEBT-004-source.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"=== {result['title']} ===\n")
        f.write(f"=== URL: https://www.moltbook.com/post/4b64728c ===\n")
        f.write(f"=== 获取时间: 2026-02-16 ===\n\n")
        f.write(result['text'])
    
    print(f"✅ 内容已保存到 {output_path}")
    print(f"\n🔍 内容预览 (前1000字符):")
    print("=" * 60)
    print(result['text'][:1000])
    print("=" * 60)

if __name__ == '__main__':
    main()
