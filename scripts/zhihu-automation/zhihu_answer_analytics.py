#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知乎回答数据分析工具
功能：分析回答数据，生成统计报告，识别优质内容和趋势话题
"""

import asyncio
import logging
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
from playwright.async_api import async_playwright, Page, Browser
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ZhihuAnswerAnalytics:
    """知乎回答数据分析器"""
    
    def __init__(self, data_dir: str = "data/zhihu"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据存储路径
        self.answers_file = self.data_dir / "answers.json"
        self.answer_stats_file = self.data_dir / "answer_stats.csv"
        self.report_dir = self.data_dir / "reports"
        self.report_dir.mkdir(exist_ok=True)
        
        self.browser: Optional[Browser] = None
    
    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox']
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
        """创建新页面"""
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        return await context.new_page()
    
    async def fetch_answers(
        self,
        question_url: str,
        max_answers: int = 50
    ) -> List[Dict]:
        """抓取指定问题的回答"""
        if not self.browser:
            await self.start()
        
        page = await self._create_page()
        answers = []
        
        try:
            logger.info(f"抓取问题回答: {question_url}")
            await page.goto(question_url, wait_until='networkidle')
            
            # 等待回答加载
            await page.wait_for_selector('.List-item', timeout=10000)
            
            # 获取所有回答
            items = await page.query_selector_all('.List-item')
            
            for idx, item in enumerate(items[:max_answers], 1):
                try:
                    answer_data = await self._parse_answer(item, idx)
                    answers.append(answer_data)
                    logger.debug(f"解析第 {idx} 个回答")
                except Exception as e:
                    logger.warning(f"解析第 {idx} 个回答失败: {e}")
            
            logger.info(f"成功抓取 {len(answers)} 个回答")
            
        except Exception as e:
            logger.error(f"抓取回答失败: {e}")
        finally:
            await page.close()
        
        return answers
    
    async def _parse_answer(self, item, rank: int) -> Dict:
        """解析单个回答"""
        answer_data = {
            'rank': rank,
            'fetch_time': datetime.now().isoformat(),
        }
        
        # 获取作者信息
        author_elem = await item.query_selector('.AuthorInfo-name')
        if author_elem:
            answer_data['author_name'] = await author_elem.inner_text()
        
        author_link = await item.query_selector('.AuthorInfo-name a')
        if author_link:
            href = await author_link.get_attribute('href')
            if href:
                answer_data['author_url'] = href if href.startswith('http') else f'https://www.zhihu.com{href}'
        
        # 获取作者标题（认证信息等）
        author_title = await item.query_selector('.AuthorInfo-headline')
        if author_title:
            answer_data['author_title'] = (await author_title.inner_text()).strip()
        
        # 获取投票数
        vote_elem = await item.query_selector('.VoteButton--up .VoteButton-label')
        if vote_elem:
            vote_text = await vote_elem.inner_text()
            answer_data['vote_count'] = self._parse_number(vote_text)
        
        # 获取内容摘要
        content_elem = await item.query_selector('.RichContent-inner')
        if content_elem:
            full_content = await content_elem.inner_text()
            answer_data['content'] = full_content[:500]  # 只保存前500字
            answer_data['content_length'] = len(full_content)
        
        # 获取评论数
        comment_elem = await item.query_selector('.ContentItem-actions Button:nth-child(2)')
        if comment_elem:
            comment_text = await comment_elem.inner_text()
            answer_data['comment_count'] = self._parse_number(comment_text)
        
        # 获取发布时间
        time_elem = await item.query_selector('.ContentItem-time')
        if time_elem:
            answer_data['publish_time'] = await time_elem.inner_text()
        
        # 获取感谢数
        thanks_elem = await item.query_selector('.ContentItem-actions Button:nth-child(3)')
        if thanks_elem:
            thanks_text = await thanks_elem.inner_text()
            answer_data['thanks_count'] = self._parse_number(thanks_text)
        
        # 获取收藏数（如果可见）
        favor_elem = await item.query_selector('.ContentItem-actions Button:nth-child(4)')
        if favor_elem:
            favor_text = await favor_elem.inner_text()
            answer_data['favor_count'] = self._parse_number(favor_text)
        
        # 判断是否为作者精选回答
        pin_elem = await item.query_selector('.ContentItem-pinInfo')
        if pin_elem:
            answer_data['is_pinned'] = True
        
        return answer_data
    
    def _parse_number(self, text: str) -> int:
        """解析数字文本"""
        text = text.strip()
        if not text or text == '评论':
            return 0
        if '万' in text:
            return int(float(text.replace('万', '')) * 10000)
        text = text.replace(',', '').replace('K', '000')
        return int(''.join(filter(str.isdigit, text))) or 0
    
    def save_answers(self, question_url: str, answers: List[Dict]):
        """保存回答数据"""
        from urllib.parse import urlparse
        question_id = urlparse(question_url).path.split('/')[-1]
        
        data = {
            'question_url': question_url,
            'question_id': question_id,
            'fetch_time': datetime.now().isoformat(),
            'count': len(answers),
            'answers': answers
        }
        
        # 保存到文件
        file_path = self.data_dir / f"answers_{question_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 更新索引文件
        self._update_answer_index(question_id, file_path, len(answers))
        
        logger.info(f"回答数据已保存到 {file_path}")
        return file_path
    
    def _update_answer_index(self, question_id: str, file_path: Path, count: int):
        """更新回答索引"""
        index_file = self.data_dir / "answers_index.json"
        index = {}
        
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        
        if question_id not in index:
            index[question_id] = []
        
        index[question_id].append({
            'file_path': str(file_path),
            'count': count,
            'fetch_time': datetime.now().isoformat()
        })
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def calculate_statistics(self, answers: List[Dict]) -> Dict:
        """计算回答统计指标"""
        if not answers:
            return {}
        
        votes = [a.get('vote_count', 0) for a in answers]
        comments = [a.get('comment_count', 0) for a in answers]
        lengths = [a.get('content_length', 0) for a in answers]
        
        stats = {
            'total_answers': len(answers),
            'vote_stats': {
                'total': sum(votes),
                'avg': np.mean(votes),
                'median': np.median(votes),
                'max': max(votes),
                'min': min(votes),
                'std': np.std(votes) if len(votes) > 1 else 0
            },
            'comment_stats': {
                'total': sum(comments),
                'avg': np.mean(comments),
                'median': np.median(comments),
                'max': max(comments)
            },
            'content_stats': {
                'avg_length': np.mean(lengths),
                'median_length': np.median(lengths),
                'max_length': max(lengths)
            }
        }
        
        # 找出最受欢迎的回答
        sorted_by_votes = sorted(answers, key=lambda x: x.get('vote_count', 0), reverse=True)
        stats['top_answers'] = sorted_by_votes[:5]
        
        return stats
    
    def identify_trending_authors(self, answers: List[Dict], min_answers: int = 2) -> List[Dict]:
        """识别热门作者"""
        author_stats = defaultdict(lambda: {
            'answers': [],
            'total_votes': 0,
            'total_comments': 0
        })
        
        for answer in answers:
            author = answer.get('author_name', '未知作者')
            author_stats[author]['answers'].append(answer)
            author_stats[author]['total_votes'] += answer.get('vote_count', 0)
            author_stats[author]['total_comments'] += answer.get('comment_count', 0)
        
        # 筛选有多个回答的作者
        trending_authors = []
        for author, stats in author_stats.items():
            if len(stats['answers']) >= min_answers:
                trending_authors.append({
                    'author_name': author,
                    'answer_count': len(stats['answers']),
                    'total_votes': stats['total_votes'],
                    'avg_votes': stats['total_votes'] / len(stats['answers']),
                    'total_comments': stats['total_comments']
                })
        
        # 按平均票数排序
        trending_authors.sort(key=lambda x: x['avg_votes'], reverse=True)
        return trending_authors[:10]
    
    def extract_keywords(self, answers: List[Dict], top_n: int = 20) -> List[Tuple[str, int]]:
        """提取关键词（简单词频统计）"""
        import jieba
        
        all_text = ' '.join([a.get('content', '') for a in answers])
        words = jieba.cut(all_text)
        
        # 过滤停用词和短词
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', 
                    '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', 
                    '看', '好', '自己', '这'}
        
        word_freq = Counter()
        for word in words:
            if len(word) > 1 and word not in stopwords:
                word_freq[word] += 1
        
        return word_freq.most_common(top_n)
    
    def generate_report(
        self,
        question_url: str,
        answers: List[Dict],
        output_format: str = 'json'
    ) -> str:
        """生成分析报告"""
        stats = self.calculate_statistics(answers)
        trending_authors = self.identify_trending_authors(answers)
        keywords = self.extract_keywords(answers)
        
        report = {
            'question_url': question_url,
            'report_time': datetime.now().isoformat(),
            'statistics': stats,
            'trending_authors': trending_authors,
            'top_keywords': [{'word': w, 'count': c} for w, c in keywords]
        }
        
        # 生成报告文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'json':
            report_file = self.report_dir / f"report_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        
        elif output_format == 'html':
            report_file = self.report_dir / f"report_{timestamp}.html"
            html_content = self._generate_html_report(report)
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        elif output_format == 'markdown':
            report_file = self.report_dir / f"report_{timestamp}.md"
            markdown_content = self._generate_markdown_report(report)
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        logger.info(f"报告已生成: {report_file}")
        return str(report_file)
    
    def _generate_html_report(self, report: Dict) -> str:
        """生成HTML格式报告"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>知乎回答分析报告</title>
    <style>
        body {{ font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; margin: 20px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #0066FF; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f5f8fa; padding: 15px; border-radius: 8px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #0066FF; }}
        .stat-label {{ color: #666; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #0066FF; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .tag {{ background: #e6f7ff; color: #0066FF; padding: 2px 8px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 知乎回答分析报告</h1>
        <p><strong>生成时间:</strong> {report['report_time']}</p>
        <p><strong>问题链接:</strong> <a href="{report['question_url']}" target="_blank">{report['question_url']}</a></p>
        
        <h2>📈 数据统计</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{report['statistics'].get('total_answers', 0)}</div>
                <div class="stat-label">回答总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report['statistics']['vote_stats']['total']:,}</div>
                <div class="stat-label">总赞同数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report['statistics']['comment_stats']['total']:,}</div>
                <div class="stat-label">总评论数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report['statistics']['vote_stats']['avg']:.1f}</div>
                <div class="stat-label">平均赞同数</div>
            </div>
        </div>
        
        <h2>🏆 热门作者</h2>
        <table>
            <thead>
                <tr>
                    <th>排名</th>
                    <th>作者</th>
                    <th>回答数</th>
                    <th>总赞同</th>
                    <th>平均赞同</th>
                </tr>
            </thead>
            <tbody>
"""
        for idx, author in enumerate(report['trending_authors'][:10], 1):
            html += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{author['author_name']}</td>
                    <td>{author['answer_count']}</td>
                    <td>{author['total_votes']:,}</td>
                    <td>{author['avg_votes']:.1f}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
        
        <h2>🔥 热门关键词</h2>
        <p>
"""
        for kw in report['top_keywords'][:15]:
            html += f'<span class="tag">{kw["word"]} × {kw["count"]}</span> '
        
        html += """
        </p>
        
        <h2>📌 TOP 5 回答</h2>
        <table>
            <thead>
                <tr>
                    <th>排名</th>
                    <th>作者</th>
                    <th>赞同数</th>
                    <th>评论数</th>
                    <th>内容长度</th>
                </tr>
            </thead>
            <tbody>
"""
        for idx, answer in enumerate(report['statistics'].get('top_answers', [])[:5], 1):
            html += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{answer.get('author_name', '未知')}</td>
                    <td>{answer.get('vote_count', 0):,}</td>
                    <td>{answer.get('comment_count', 0):,}</td>
                    <td>{answer.get('content_length', 0)}字</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """生成Markdown格式报告"""
        md = f"""# 📊 知乎回答分析报告

**生成时间:** {report['report_time']}
**问题链接:** [{report['question_url']}]({report['question_url']})

## 📈 数据统计

| 指标 | 数值 |
|------|------|
| 回答总数 | {report['statistics'].get('total_answers', 0)} |
| 总赞同数 | {report['statistics']['vote_stats']['total']:,} |
| 总评论数 | {report['statistics']['comment_stats']['total']:,} |
| 平均赞同数 | {report['statistics']['vote_stats']['avg']:.1f} |

## 🏆 热门作者

| 排名 | 作者 | 回答数 | 总赞同 | 平均赞同 |
|------|------|--------|--------|----------|
"""
        for idx, author in enumerate(report['trending_authors'][:10], 1):
            md += f"| {idx} | {author['author_name']} | {author['answer_count']} | {author['total_votes']:,} | {author['avg_votes']:.1f} |\n"
        
        md += "\n## 🔥 热门关键词\n\n"
        for kw in report['top_keywords'][:15]:
            md += f"- {kw['word']} × {kw['count']}\n"
        
        md += "\n## 📌 TOP 5 回答\n\n"
        md += "| 排名 | 作者 | 赞同数 | 评论数 | 内容长度 |\n"
        md += "|------|------|--------|--------|----------|\n"
        for idx, answer in enumerate(report['statistics'].get('top_answers', [])[:5], 1):
            md += f"| {idx} | {answer.get('author_name', '未知')} | {answer.get('vote_count', 0):,} | {answer.get('comment_count', 0):,} | {answer.get('content_length', 0)}字 |\n"
        
        return md
    
    def compare_timeframes(self, older_answers: List[Dict], newer_answers: List[Dict]) -> Dict:
        """比较两个时间点的回答数据"""
        comparison = {
            'older_count': len(older_answers),
            'newer_count': len(newer_answers),
            'growth': len(newer_answers) - len(older_answers),
            'growth_rate': ((len(newer_answers) - len(older_answers)) / len(older_answers) * 100) if older_answers else 0
        }
        
        # 比较赞同数变化
        old_votes = sum(a.get('vote_count', 0) for a in older_answers)
        new_votes = sum(a.get('vote_count', 0) for a in newer_answers)
        comparison['vote_growth'] = new_votes - old_votes
        
        return comparison


async def main():
    """主函数 - 演示用法"""
    analyzer = ZhihuAnswerAnalytics()
    example_url = "https://www.zhihu.com/question/123456"
    
    print("知乎回答数据分析工具")
    print(f"示例问题: {example_url}")
    print("\n使用方法:")
    print("1. 首先抓取回答: analyzer.fetch_answers(question_url)")
    print("2. 保存数据: analyzer.save_answers(question_url, answers)")
    print("3. 生成报告: analyzer.generate_report(question_url, answers)")


if __name__ == '__main__':
    asyncio.run(main())
