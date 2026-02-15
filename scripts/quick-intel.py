#!/usr/bin/env python3
"""
简化版情报收集 - 使用Playwright
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

async def collect_hackernews():
    """收集Hacker News热门内容"""
    print("📡 Hacker News...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path='/usr/bin/chromium')
        page = await browser.new_page()
        
        try:
            await page.goto('https://news.ycombinator.com', timeout=15000)
            
            items = await page.query_selector_all('.athing')
            results = []
            
            for i, item in enumerate(items[:10]):
                try:
                    title_elem = await item.query_selector('.titleline > a')
                    title = await title_elem.inner_text() if title_elem else ""
                    url = await title_elem.get_attribute('href') if title_elem else ""
                    
                    # 获取分数 - 找到对应的score元素
                    item_id = await item.get_attribute('id')
                    score_elem = await page.query_selector(f'#score_{item_id}')
                    score = "0"
                    if score_elem:
                        score_text = await score_elem.inner_text()
                        score = score_text.split()[0] if score_text else "0"
                    
                    results.append({'title': title[:100], 'url': url[:200], 'score': score})
                    print(f"  {i+1}. {title[:50]}... ({score})")
                except Exception as e:
                    continue
            
            await browser.close()
            
            intel_dir = Path("memory/intel")
            intel_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = intel_dir / f"intel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump({'time': datetime.now().isoformat(), 'items': results}, f)
            
            print(f"✅ 保存 {len(results)} 条")
            return results
            
        except Exception as e:
            print(f"❌ {e}")
            await browser.close()
            return []

if __name__ == "__main__":
    asyncio.run(collect_hackernews())
