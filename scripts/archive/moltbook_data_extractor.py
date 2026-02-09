#!/usr/bin/env python3
"""
Moltbook 数据提取脚本
使用 Playwright 提取用户主页的帖子数据

功能：
1. 访问 Moltbook 用户主页
2. 提取帖子标题、点赞数、评论数、发布时间
3. 输出为结构化 JSON
4. 截图作为备份

使用方法：
    python moltbook_data_extractor.py
    python moltbook_data_extractor.py --user LinLin_v1
    python moltbook_data_extractor.py --user LinLin_v1 --headless --output data.json

安装依赖：
    pip install playwright
    playwright install
"""

import json
import argparse
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, ElementHandle


class MoltbookExtractor:
    """Moltbook 数据提取器"""
    
    BASE_URL = "https://www.moltbook.com/u/"
    
    # 常见选择器模式（根据实际页面结构调整）
    SELECTORS = {
        # 帖子容器 - 尝试多种常见模式
        "post_containers": [
            '[data-testid="post"]',           # data-testid 模式
            '.post',                           # class 模式
            '.feed-item',                      # feed 模式
            'article',                         # semantic 标签
            '[class*="post"]',                # 包含 post 的 class
            '[class*="card"]',                # 包含 card 的 class
            '.pin-item',                       # 瀑布流模式
        ],
        # 帖子标题
        "title": [
            'h1', 'h2', 'h3', '.title', '[class*="title"]',
            '.content-title', '.post-title', 'p[class*="title"]'
        ],
        # 点赞数
        "likes": [
            '[data-testid="like-count"]', '.like-count', '.likes',
            '[class*="like"] [class*="count"]', '[class*="like-count"]',
            'button:has-text("赞") + span', '.action-item:has-text("赞")'
        ],
        # 评论数
        "comments": [
            '[data-testid="comment-count"]', '.comment-count', '.comments',
            '[class*="comment"] [class*="count"]', '[class*="comment-count"]',
            'button:has-text("评论") + span', '.action-item:has-text("评论")'
        ],
        # 发布时间
        "publish_time": [
            'time', '[datetime]', '.time', '.date',
            '[class*="time"]', '[class*="date"]', '.publish-time',
            '.create-time', '[class*="create-time"]'
        ]
    }
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.page: Optional[Page] = None
        self.browser = None
        self.context = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.0'
        )
        self.page = await self.context.new_page()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def navigate(self, username: str) -> bool:
        """导航到用户主页"""
        url = f"{self.BASE_URL}{username}"
        print(f"[INFO] 正在访问: {url}")
        
        try:
            response = await self.page.goto(url, wait_until='networkidle', timeout=self.timeout)
            
            if response and response.status == 404:
                print(f"[ERROR] 用户 {username} 不存在 (404)")
                return False
            
            # 等待页面加载完成
            await self.page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)  # 给动态内容加载时间
            
            print(f"[INFO] 页面加载完成，状态码: {response.status if response else 'N/A'}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 导航失败: {e}")
            return False
    
    async def scroll_to_load(self, max_scrolls: int = 5) -> int:
        """
        滚动页面加载更多内容
        
        Args:
            max_scrolls: 最大滚动次数
            
        Returns:
            滚动后页面高度
        """
        print(f"[INFO] 开始滚动加载，最大滚动次数: {max_scrolls}")
        
        for i in range(max_scrolls):
            prev_height = await self.page.evaluate('document.body.scrollHeight')
            
            # 滚动到底部
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1.5)  # 等待内容加载
            
            new_height = await self.page.evaluate('document.body.scrollHeight')
            
            if new_height == prev_height:
                print(f"[INFO] 滚动 {i+1} 次后到达底部")
                break
                
            print(f"[INFO] 第 {i+1} 次滚动，页面高度: {new_height}")
        
        return await self.page.evaluate('document.body.scrollHeight')
    
    async def find_posts(self) -> List[ElementHandle]:
        """查找所有帖子元素"""
        posts = []
        
        for selector in self.SELECTORS["post_containers"]:
            try:
                elements = await self.page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    print(f"[INFO] 使用选择器 '{selector}' 找到 {len(elements)} 个帖子")
                    posts = elements
                    break
            except Exception as e:
                continue
        
        if not posts:
            # 如果常规选择器失败，尝试更通用的方法
            print("[WARN] 常规选择器未找到帖子，尝试通用方法...")
            
            # 查找可能包含点赞/评论按钮的容器
            possible_posts = await self.page.query_selector_all('article, .card, [class*="item"]')
            if possible_posts:
                print(f"[INFO] 通用方法找到 {len(possible_posts)} 个可能的帖子")
                posts = possible_posts
        
        return posts
    
    async def extract_text(self, element: ElementHandle, selectors: List[str]) -> Optional[str]:
        """尝试多个选择器提取文本"""
        for selector in selectors:
            try:
                # 在元素内查找
                el = await element.query_selector(selector)
                if el:
                    text = await el.text_content()
                    if text:
                        return text.strip()
            except:
                continue
        return None
    
    async def extract_number(self, text: Optional[str]) -> Optional[int]:
        """从文本中提取数字"""
        if not text:
            return None
        
        import re
        # 提取数字（支持千分位）
        numbers = re.findall(r'[\d,]+', text.replace(',', ''))
        if numbers:
            try:
                return int(numbers[0])
            except:
                pass
        return None
    
    async def extract_post_data(self, post: ElementHandle, index: int) -> Dict:
        """提取单个帖子的数据"""
        data = {
            "index": index,
            "title": None,
            "likes": None,
            "comments": None,
            "publish_time": None,
            "raw_likes_text": None,
            "raw_comments_text": None
        }
        
        try:
            # 提取标题
            title = await self.extract_text(post, self.SELECTORS["title"])
            if title:
                data["title"] = title[:500]  # 限制长度
            
            # 提取点赞数
            likes_text = await self.extract_text(post, self.SELECTORS["likes"])
            data["raw_likes_text"] = likes_text
            data["likes"] = await self.extract_number(likes_text)
            
            # 提取评论数
            comments_text = await self.extract_text(post, self.SELECTORS["comments"])
            data["raw_comments_text"] = comments_text
            data["comments"] = await self.extract_number(comments_text)
            
            # 提取发布时间
            publish_time = await self.extract_text(post, self.SELECTORS["publish_time"])
            if not publish_time:
                # 尝试从 time 标签的 datetime 属性获取
                time_el = await post.query_selector('time')
                if time_el:
                    publish_time = await time_el.get_attribute('datetime')
            data["publish_time"] = publish_time
            
        except Exception as e:
            print(f"[WARN] 提取第 {index} 个帖子时出错: {e}")
        
        return data
    
    async def take_screenshot(self, path: str):
        """截取页面截图作为备份"""
        try:
            await self.page.screenshot(path=path, full_page=True)
            print(f"[INFO] 截图已保存: {path}")
        except Exception as e:
            print(f"[ERROR] 截图失败: {e}")
    
    async def extract(self, username: str, scroll: bool = True, 
                      max_scrolls: int = 5) -> Dict:
        """
        主提取方法
        
        Args:
            username: Moltbook 用户名
            scroll: 是否滚动加载更多内容
            max_scrolls: 最大滚动次数
            
        Returns:
            包含提取数据的字典
        """
        result = {
            "source": "moltbook",
            "username": username,
            "url": f"{self.BASE_URL}{username}",
            "extraction_time": datetime.now().isoformat(),
            "total_posts": 0,
            "posts": [],
            "screenshot": None,
            "errors": []
        }
        
        try:
            # 导航到用户主页
            if not await self.navigate(username):
                result["errors"].append(f"Failed to navigate to user page: {username}")
                return result
            
            # 滚动加载（可选）
            if scroll:
                await self.scroll_to_load(max_scrolls)
            
            # 查找所有帖子
            posts = await self.find_posts()
            result["total_posts"] = len(posts)
            
            if not posts:
                result["errors"].append("No posts found on the page")
                print("[WARN] 未找到任何帖子")
            
            # 提取每个帖子的数据
            print(f"[INFO] 开始提取 {len(posts)} 个帖子的数据...")
            for i, post in enumerate(posts, 1):
                data = await self.extract_post_data(post, i)
                result["posts"].append(data)
                
                if i % 10 == 0:
                    print(f"[INFO] 已提取 {i}/{len(posts)} 个帖子")
            
            print(f"[INFO] 提取完成，共 {len(posts)} 个帖子")
            
        except Exception as e:
            error_msg = f"Extraction error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            result["errors"].append(error_msg)
        
        return result


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='提取 Moltbook 用户主页数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python moltbook_data_extractor.py
    python moltbook_data_extractor.py --user LinLin_v1
    python moltbook_data_extractor.py --user LinLin_v1 --headless --scroll --max-scrolls 3
    python moltbook_data_extractor.py --user LinLin_v1 --output data.json --screenshot backup.png
        """
    )
    
    parser.add_argument('--user', '-u', default='LinLin_v1',
                        help='目标用户名 (默认: LinLin_v1)')
    parser.add_argument('--output', '-o', default='moltbook_data.json',
                        help='JSON 输出文件路径 (默认: moltbook_data.json)')
    parser.add_argument('--screenshot', '-s', default=None,
                        help='截图保存路径 (默认: moltbook_<用户名>_<时间戳>.png)')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='无头模式运行 (默认: True)')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                        help='显示浏览器窗口')
    parser.add_argument('--scroll', action='store_true', default=True,
                        help='滚动加载更多内容 (默认: True)')
    parser.add_argument('--no-scroll', action='store_false', dest='scroll',
                        help='不滚动加载')
    parser.add_argument('--max-scrolls', type=int, default=5,
                        help='最大滚动次数 (默认: 5)')
    parser.add_argument('--timeout', type=int, default=30000,
                        help='页面加载超时时间(ms) (默认: 30000)')
    
    args = parser.parse_args()
    
    # 设置默认截图路径
    if args.screenshot is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.screenshot = f"moltbook_{args.user}_{timestamp}.png"
    
    print("=" * 60)
    print("Moltbook 数据提取器")
    print("=" * 60)
    print(f"目标用户: {args.user}")
    print(f"无头模式: {args.headless}")
    print(f"滚动加载: {args.scroll}")
    print(f"输出文件: {args.output}")
    print(f"截图文件: {args.screenshot}")
    print("=" * 60)
    
    # 执行提取
    async with MoltbookExtractor(headless=args.headless, timeout=args.timeout) as extractor:
        result = await extractor.extract(
            username=args.user,
            scroll=args.scroll,
            max_scrolls=args.max_scrolls
        )
        
        # 截图备份
        await extractor.take_screenshot(args.screenshot)
        result["screenshot"] = args.screenshot
        
        # 保存 JSON
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"[SUCCESS] 数据已保存到: {args.output}")
        except Exception as e:
            print(f"[ERROR] 保存 JSON 失败: {e}")
        
        # 打印摘要
        print("\n" + "=" * 60)
        print("提取摘要")
        print("=" * 60)
        print(f"总帖子数: {result['total_posts']}")
        print(f"成功提取: {len([p for p in result['posts'] if p.get('title')])}")
        print(f"包含点赞数据: {len([p for p in result['posts'] if p.get('likes') is not None])}")
        print(f"包含评论数据: {len([p for p in result['posts'] if p.get('comments') is not None])}")
        if result['errors']:
            print(f"\n错误: {len(result['errors'])}")
            for err in result['errors']:
                print(f"  - {err}")
        print("=" * 60)
        
        # 打印前3个帖子的预览
        if result['posts']:
            print("\n前3个帖子预览:")
            for post in result['posts'][:3]:
                print(f"\n  [{post['index']}] {post['title'][:50] if post['title'] else 'N/A'}...")
                print(f"      点赞: {post['likes']}, 评论: {post['comments']}, 时间: {post['publish_time']}")


if __name__ == '__main__':
    asyncio.run(main())
