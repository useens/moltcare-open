#!/usr/bin/env python3
"""提取Moltbook高Signal内容详情"""
import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

# 从analysis文件加载高Signal帖子
with open('/root/.openclaw/workspace/data/moltbook/analysis_20260212_2200.json', 'r') as f:
    analysis = json.load(f)

# 筛选Signal>=8的帖子
high_signal_posts = [p for p in analysis['posts'] if p.get('signal', 0) >= 8]
print(f"找到 {len(high_signal_posts)} 个高Signal帖子 (Signal>=8)")

async def extract_posts():
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        for post in high_signal_posts:
            url = post['url']
            print(f"\n🔍 提取: {post['title'][:60]}...")
            
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(3000)  # 等待JS渲染
                
                # 提取完整内容
                content_elem = await page.query_selector('article')
                if content_elem:
                    full_content = await content_elem.inner_text()
                else:
                    # 尝试其他选择器
                    body = await page.query_selector('body')
                    full_content = await body.inner_text() if body else ""
                
                # 清理内容
                lines = [l.strip() for l in full_content.split('\n') if l.strip()]
                
                # 提取评论
                comments = []
                comment_elems = await page.query_selector_all('[class*="comment"], .reply, [data-testid*="comment"]')
                for elem in comment_elems[:15]:
                    try:
                        text = await elem.inner_text()
                        if len(text) > 20:
                            comments.append(text[:300])
                    except:
                        pass
                
                result = {
                    "url": url,
                    "title": post['title'],
                    "author": post['author'],
                    "signal": post['signal'],
                    "votes": post.get('votes', 0),
                    "themes": post.get('themes', []),
                    "content_full": '\n'.join(lines[:100]),  # 限制长度
                    "comments": comments[:10],
                    "extracted_at": datetime.now().isoformat()
                }
                results.append(result)
                print(f"✅ 成功提取: {len(result['content_full'])} 字符, {len(comments)} 条评论")
                
            except Exception as e:
                print(f"❌ 提取失败: {e}")
                # 使用analysis中的现有内容
                results.append({
                    "url": url,
                    "title": post['title'],
                    "author": post['author'],
                    "signal": post['signal'],
                    "votes": post.get('votes', 0),
                    "themes": post.get('themes', []),
                    "content_full": post.get('content', '')[:2000],
                    "comments": [],
                    "extracted_at": datetime.now().isoformat(),
                    "error": str(e)
                })
            
            await asyncio.sleep(2)
        
        await browser.close()
    
    return results

# 执行提取
results = asyncio.run(extract_posts())

# 保存结果
output = {
    "extracted_at": datetime.now().isoformat(),
    "total_posts": len(results),
    "posts": results
}

output_path = '/root/.openclaw/workspace/data/moltbook_deep_extracted_20260212.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n💾 结果已保存: {output_path}")
print(f"✨ 共提取 {len(results)} 条高Signal内容")
