#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎热榜监控工具 - Playwright实现
功能：实时抓取知乎热榜，支持数据缓存和历史趋势分析
"""

import asyncio
import logging
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
import aiofiles

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ZhihuHotMonitor:
    """知乎热榜监控器"""
    
    def __init__(
        self,
        data_dir: str = "data/zhihu",
        max_items: int = 50,
        headless: bool = True
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_items = max_items
        self.headless = headless
        self.browser: Optional[Browser] = None
        
        # 数据存储路径
        self.hotlist_file = self.data_dir / "hotlist.json"
        self.history_file = self.data_dir / "history.csv"
        self.trend_file = self.data_dir / "trends.json"
        
        # 初始化历史记录文件
        self._init_history_file()
    
    def _init_history_file(self):
        """初始化历史记录CSV文件"""
        if not self.history_file.exists():
            with open(self.history_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'rank', 'question_id', 'question_title',
                    'description', 'hot_score', 'answer_count', 'follower_count',
                    'category', 'is_top'
                ])
    
    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox'
            ]
        )
        logger.info("浏览器已启动")
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("浏览器已关闭")
    
    async def _create_page(self) -> Page:
        """创建新页面并设置用户代理"""
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # 设置额外的headers
        await page.set_extra_http_headers({
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        return page
    
    async def fetch_hotlist(self) -> List[Dict]:
        """抓取知乎热榜数据"""
        if not self.browser:
            await self.start()
        
        page = await self._create_page()
        hot_items = []
        
        try:
            logger.info("开始抓取知乎热榜...")
            await page.goto('https://www.zhihu.com/hot', wait_until='networkidle')
            
            # 等待热榜加载
            await page.wait_for_selector('.HotItem', timeout=10000)
            
            # 获取所有热榜条目
            items = await page.query_selector_all('.HotItem')
            
            for idx, item in enumerate(items[:self.max_items], 1):
                try:
                    item_data = await self._parse_hot_item(item, idx)
                    hot_items.append(item_data)
                    logger.info(f"解析第 {idx} 条: {item_data['question_title'][:30]}...")
                except Exception as e:
                    logger.warning(f"解析第 {idx} 条失败: {e}")
            
            logger.info(f"成功抓取 {len(hot_items)} 条热榜数据")
            
        except Exception as e:
            logger.error(f"抓取热榜失败: {e}")
        finally:
            await page.close()
        
        return hot_items
    
    async def _parse_hot_item(self, item, rank: int) -> Dict:
        """解析单个热榜条目"""
        item_data = {
            'rank': rank,
            'timestamp': datetime.now().isoformat(),
        }
        
        # 获取标题和链接
        title_elem = await item.query_selector('.HotItem-title a')
        if title_elem:
            item_data['question_title'] = await title_elem.inner_text()
            href = await title_elem.get_attribute('href')
            if href:
                item_data['question_url'] = href if href.startswith('http') else f'https://www.zhihu.com{href}'
                # 提取问题ID
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(item_data['question_url'])
                item_data['question_id'] = parsed.path.split('/')[-1]
        
        # 获取描述
        desc_elem = await item.query_selector('.HotItem-excerpt')
        if desc_elem:
            item_data['description'] = (await desc_elem.inner_text()).strip()
        
        # 获取热度值
        hot_elem = await item.query_selector('.HotItem-metrics')
        if hot_elem:
            hot_text = await hot_elem.inner_text()
            hot_score = self._parse_hot_score(hot_text)
            item_data['hot_score'] = hot_score
        
        # 获取分类标签
        category_elem = await item.query_selector('.Tag::text')
        if category_elem:
            item_data['category'] = await category_elem.inner_text()
        
        # 是否置顶
        if rank == 1:
            item_data['is_top'] = True
        
        return item_data
    
    def _parse_hot_score(self, text: str) -> int:
        """解析热度文本为数字"""
        text = text.strip()
        if '万' in text:
            return int(float(text.replace('万', '')) * 10000)
        return int(text.replace(',', ''))
    
    async def fetch_hotlist_api(self) -> List[Dict]:
        """通过API获取热榜数据（备用方案）"""
        import httpx
        
        api_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                hot_items = []
                for idx, item in enumerate(data.get('data', [])[:self.max_items], 1):
                    target = item.get('target', {})
                    hot_items.append({
                        'rank': idx,
                        'timestamp': datetime.now().isoformat(),
                        'question_id': target.get('id', ''),
                        'question_title': target.get('title', ''),
                        'description': target.get('excerpt', ''),
                        'hot_score': item.get('detail_text', ''),
                        'answer_count': target.get('answer_count', 0),
                        'follower_count': target.get('follower_count', 0),
                    })
                
                return hot_items
        except Exception as e:
            logger.error(f"API获取失败: {e}")
            return []
    
    def save_hotlist(self, hot_items: List[Dict]):
        """保存热榜数据到JSON"""
        data = {
            'fetch_time': datetime.now().isoformat(),
            'count': len(hot_items),
            'items': hot_items
        }
        
        with open(self.hotlist_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 同时保存时间戳版本
        timestamp_file = self.data_dir / f"hotlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(timestamp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"热榜数据已保存到 {self.hotlist_file}")
    
    def append_history(self, hot_items: List[Dict]):
        """追加历史数据到CSV"""
        timestamp = datetime.now().isoformat()
        
        with open(self.history_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for item in hot_items:
                writer.writerow([
                    timestamp,
                    item.get('rank', ''),
                    item.get('question_id', ''),
                    item.get('question_title', ''),
                    item.get('description', ''),
                    item.get('hot_score', ''),
                    item.get('answer_count', ''),
                    item.get('follower_count', ''),
                    item.get('category', ''),
                    item.get('is_top', False)
                ])
        
        logger.info(f"已追加 {len(hot_items)} 条历史记录")
    
    def calculate_trends(self, days: int = 7) -> Dict:
        """计算热榜趋势"""
        if not self.history_file.exists():
            return {}
        
        from collections import defaultdict
        
        trends = defaultdict(lambda: {'scores': [], 'ranks': []})
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with open(self.history_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    timestamp = datetime.fromisoformat(row['timestamp'])
                    if timestamp >= cutoff_date:
                        question_id = row['question_id']
                        if row['hot_score'].isdigit():
                            trends[question_id]['scores'].append({
                                'time': timestamp.isoformat(),
                                'score': int(row['hot_score']),
                                'rank': int(row['rank'])
                            })
                except:
                    continue
        
        # 计算趋势指标
        trend_analysis = {}
        for qid, data in trends.items():
            if len(data['scores']) >= 3:
                scores = [s['score'] for s in data['scores']]
                ranks = [s['rank'] for s in data['scores']]
                trend_analysis[qid] = {
                    'question_id': qid,
                    'current_score': scores[-1],
                    'current_rank': ranks[-1],
                    'score_change': scores[-1] - scores[0],
                    'rank_change': ranks[0] - ranks[-1],  # 正值表示排名上升
                    'avg_score': sum(scores) / len(scores),
                    'sample_count': len(scores),
                    'trend': '上升' if scores[-1] > scores[-2] else '下降'
                }
        
        return trend_analysis
    
    async def monitor(
        self,
        interval_minutes: int = 60,
        max_runs: Optional[int] = None
    ):
        """持续监控热榜"""
        run_count = 0
        
        while True:
            if max_runs and run_count >= max_runs:
                logger.info(f"已达到最大运行次数 {max_runs}")
                break
            
            run_count += 1
            logger.info(f"=== 第 {run_count} 次监控 ===")
            
            # 抓取热榜
            hot_items = await self.fetch_hotlist()
            if not hot_items:
                hot_items = await self.fetch_hotlist_api()
            
            if hot_items:
                # 保存数据
                self.save_hotlist(hot_items)
                self.append_history(hot_items)
                
                # 计算趋势
                trends = self.calculate_trends()
                logger.info(f"识别到 {len(trends)} 个有趋势的问题")
            
            # 等待下次运行
            if max_runs and run_count >= max_runs:
                break
            
            wait_seconds = interval_minutes * 60
            logger.info(f"等待 {interval_minutes} 分钟后下次运行...")
            await asyncio.sleep(wait_seconds)
    
    def get_latest_hotlist(self) -> Dict:
        """获取最新热榜数据"""
        if self.hotlist_file.exists():
            with open(self.hotlist_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}


async def main():
    """主函数入口"""
    monitor = ZhihuHotMonitor(headless=False)
    
    try:
        await monitor.start()
        await monitor.monitor(interval_minutes=30, max_runs=1)
    finally:
        await monitor.close()


if __name__ == '__main__':
    asyncio.run(main())
