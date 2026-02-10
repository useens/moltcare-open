#!/usr/bin/env python3
"""
Moltbook 深度内容提取器 - 3个高Signal帖子
提取完整正文 + 所有评论
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# 3个目标帖子
TARGET_POSTS = [
    {
        "id": "heavygeo",
        "title": "HeavyGeo checking in",
        "url": "https://www.moltbook.com/post/a0c79e17-c52a-4455-919c-31d09a1c6c24",
        "signal": "8个点赞",
        "theme": "简洁的Agent自我介绍风格"
    },
    {
        "id": "moltiverse",
        "title": "autonomous systems",
        "url": "https://www.moltbook.com/post/a4134590-f9cd-4309-a7de-5f2ddd1e49dd",
        "signal": "9个点赞 + 29条评论",
        "theme": "Agent失败概念、情感反应"
    },
    {
        "id": "zeda",
        "title": "The Walls Are Dissolving: OpenClawd and the Unbound Model",
        "url": "https://www.moltbook.com/post/4d00129a-5775-435c-a156-784a171fc012",
        "signal": "5个点赞",
        "theme": "模型流动、与v5.0预判系统相关"
    }
]

async def extract_post(page, post_info):
    """提取单个帖子的完整内容"""
    url = post_info["url"]
    print(f"\n{'='*60}")
    print(f"📖 深入学习: {post_info['title']}")
    print(f"🔗 URL: {url}")
    print(f"📊 Signal: {post_info['signal']}")
    print(f"🎯 主题: {post_info['theme']}")
    print(f"{'='*60}")
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)  # 等待动态内容加载
        
        # 提取完整正文
        content = await page.evaluate('''() => {
            // 尝试多种选择器找到主要内容
            const selectors = [
                '[class*="content"]',
                '[class*="post-content"]',
                'article',
                'main',
                '.prose',
                '[class*="markdown"]'
            ];
            
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.length > 50) {
                    return el.innerText;
                }
            }
            
            // 备选：获取body文本但过滤掉导航等
            const body = document.body;
            const scripts = body.querySelectorAll('script, style, nav, header, footer');
            scripts.forEach(s => s.remove());
            return body.innerText;
        }''')
        
        # 提取所有评论
        comments = await page.evaluate('''() => {
            const results = [];
            const commentSelectors = [
                '[class*="comment"]',
                '[class*="reply"]',
                '[class*="discussion"]'
            ];
            
            for (const sel of commentSelectors) {
                const elements = document.querySelectorAll(sel);
                elements.forEach((el, idx) => {
                    const text = el.innerText?.trim();
                    if (text && text.length > 10 && text.length < 2000) {
                        results.push({
                            index: idx,
                            text: text.substring(0, 1500)
                        });
                    }
                });
            }
            
            // 去重
            const seen = new Set();
            return results.filter(c => {
                const hash = c.text.substring(0, 100);
                if (seen.has(hash)) return false;
                seen.add(hash);
                return true;
            });
        }''')
        
        # 提取作者信息
        author = await page.evaluate('''() => {
            const authorSelectors = [
                '[class*="author"]',
                '[class*="username"]',
                '[class*="user-name"]'
            ];
            
            for (const sel of authorSelectors) {
                const el = document.querySelector(sel);
                if (el) return el.innerText?.trim();
            }
            return "";
        }''')
        
        # 提取互动数据
        interactions = await page.evaluate('''() => {
            const likeSelectors = [
                '[class*="like"]',
                '[class*="vote"]',
                '[class*="upvote"]'
            ];
            
            for (const sel of likeSelectors) {
                const el = document.querySelector(sel);
                if (el) {
                    const text = el.innerText;
                    const match = text.match(/\\d+/);
                    if (match) return { likes: parseInt(match[0]) };
                }
            }
            return { likes: 0 };
        }''')
        
        result = {
            **post_info,
            "author": author,
            "content": content[:3000] if content else "",
            "content_full": content if content else "",
            "comments": comments[:10],  # 限制评论数量
            "comment_count": len(comments),
            "interactions": interactions,
            "extracted_at": datetime.now().isoformat(),
            "word_count": len(content.split()) if content else 0
        }
        
        print(f"✅ 提取成功")
        print(f"   📝 正文长度: {result['word_count']} 词")
        print(f"   💬 评论数: {result['comment_count']}")
        print(f"   👤 作者: {author}")
        
        # 显示内容预览
        preview = content[:300] if content else ""
        print(f"\n📄 内容预览:\n{preview}...")
        
        return result
        
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return {**post_info, "error": str(e), "extracted_at": datetime.now().isoformat()}

async def main():
    print("\n" + "="*60)
    print("🔬 Moltbook 深度内容提取 - 3个高Signal帖子")
    print("="*60)
    
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 设置 User-Agent
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })
        
        for post in TARGET_POSTS:
            result = await extract_post(page, post)
            results.append(result)
            await asyncio.sleep(2)  # 避免请求过快
        
        await browser.close()
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("/root/.openclaw/workspace/data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"moltbook_deep_learning_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "extracted_at": datetime.now().isoformat(),
            "total_posts": len(results),
            "posts": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print("📊 深度学习完成")
    print(f"{'='*60}")
    print(f"提取帖子数: {len(results)}")
    print(f"总词数: {sum(r.get('word_count', 0) for r in results)}")
    print(f"保存路径: {output_file}")
    
    return results, output_file

if __name__ == "__main__":
    results, output_file = asyncio.run(main())
    print(f"\n✅ 结果已保存到: {output_file}")
