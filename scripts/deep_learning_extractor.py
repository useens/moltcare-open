#!/usr/bin/env python3
"""
Deep Learning Extractor - 配合Playwright自动化收集高Signal内容
用于Moltbook等Agent社区的高价值内容深度提取
"""

import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from typing import List, Dict, Optional
import argparse

class DeepLearningExtractor:
    """深度内容提取器 - 获取高Signal内容的完整详情和评论"""
    
    def __init__(self, config_path: str = "moltbook.json"):
        self.config = self._load_config(config_path)
        self.extracted_data = []
        
    def _load_config(self, path: str) -> Dict:
        """加载配置文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def extract_post(self, page, url: str) -> Optional[Dict]:
        """提取单个帖子的完整内容"""
        try:
            print(f"🔍 正在提取: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 等待内容加载
            await page.wait_for_selector('article, .post-content, [data-testid="post"]', timeout=10000)
            
            # 提取标题
            title_elem = await page.query_selector('h1, .post-title, article h1')
            title = await title_elem.inner_text() if title_elem else "未知标题"
            
            # 提取作者
            author_elem = await page.query_selector('.author, [data-testid="author"], .username')
            author = await author_elem.inner_text() if author_elem else "未知作者"
            
            # 提取主内容
            content_elem = await page.query_selector('article, .post-content, .content')
            content = await content_elem.inner_text() if content_elem else ""
            
            # 提取评论
            comments = await self._extract_comments(page)
            
            # 统计字数
            word_count = len(content.split())
            
            return {
                "url": url,
                "title": title.strip(),
                "author": author.strip(),
                "content": content.strip(),
                "comments": comments,
                "comment_count": len(comments),
                "word_count": word_count,
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ 提取失败 {url}: {str(e)}")
            return None
    
    async def _extract_comments(self, page) -> List[Dict]:
        """提取评论列表"""
        comments = []
        try:
            comment_elems = await page.query_selector_all('.comment, [data-testid="comment"], .reply')
            
            for elem in comment_elems[:20]:  # 限制提取前20条评论
                try:
                    author_elem = await elem.query_selector('.comment-author, .username')
                    author = await author_elem.inner_text() if author_elem else "匿名"
                    
                    text_elem = await elem.query_selector('.comment-text, .text, p')
                    text = await text_elem.inner_text() if text_elem else ""
                    
                    comments.append({
                        "author": author.strip(),
                        "text": text.strip()[:500]  # 限制长度
                    })
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ 评论提取部分失败: {e}")
            
        return comments
    
    async def extract_batch(self, urls: List[str]) -> List[Dict]:
        """批量提取多个URL"""
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=self.config.get('user_agent', 'Mozilla/5.0 (compatible; DeepLearningBot/1.0)')
            )
            
            # 添加cookies（如果配置中有）
            if 'cookies' in self.config:
                await context.add_cookies(self.config['cookies'])
            
            page = await context.new_page()
            
            for url in urls:
                result = await self.extract_post(page, url)
                if result:
                    results.append(result)
                    print(f"✅ 成功提取: {result['title'][:50]}... ({result['word_count']}字)")
                await asyncio.sleep(2)  # 礼貌延迟
            
            await browser.close()
        
        return results
    
    def save_results(self, results: List[Dict], output_path: Optional[str] = None):
        """保存提取结果"""
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"data/moltbook_deep_extract_{timestamp}.json"
        
        output = {
            "extracted_at": datetime.now().isoformat(),
            "total_posts": len(results),
            "posts": results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存到: {output_path}")
        return output_path

def main():
    parser = argparse.ArgumentParser(description='深度内容提取器')
    parser.add_argument('--config', default='moltbook.json', help='配置文件路径')
    parser.add_argument('--urls', nargs='+', help='要提取的URL列表')
    parser.add_argument('--input', help='包含URL列表的JSON文件')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--min-signal', type=int, default=8, help='最小Signal分数')
    
    args = parser.parse_args()
    
    extractor = DeepLearningExtractor(args.config)
    
    # 获取URL列表
    urls = []
    if args.urls:
        urls = args.urls
    elif args.input:
        with open(args.input, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                urls = [item.get('url', item) for item in data if isinstance(item, dict) or isinstance(item, str)]
            elif isinstance(data, dict) and 'posts' in data:
                urls = [p.get('url') for p in data['posts'] if p.get('signal', 0) >= args.min_signal]
    
    if not urls:
        print("❌ 没有提供URL。使用 --urls 或 --input 参数")
        return
    
    print(f"🚀 开始深度提取 {len(urls)} 个高Signal内容...")
    
    # 执行提取
    results = asyncio.run(extractor.extract_batch(urls))
    
    # 保存结果
    extractor.save_results(results, args.output)
    
    print(f"\n✨ 提取完成! 共 {len(results)} 条内容")

if __name__ == '__main__':
    main()
