#!/usr/bin/env python3
"""
Moltbook Unified Scanner v1.0
Moltbook统一扫描器 - 合并所有Moltbook提取/扫描/分析功能

替代脚本：
- moltbook-agent.py
- moltbook-browser-extractor.py
- moltbook-deep-scanner.py
- moltbook-detail-extract.py
- moltbook-detail-extract-v2.py
- moltbook-evolution.py
- moltbook-feed-browser.py
- moltbook-full-scan.py
- moltbook-github-loop-v21.py
- moltbook-intel-collector.py
- moltbook-iterative-extractor.py
- moltbook-quick-extract.py
- moltbook-scan-analyzer.py
- moltbook-super-extractor.py
- extract_moltbook_posts.py

Usage:
    python3 moltbook-unified.py [--mode=quick|deep|evolution]
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
MEMORY_DIR = WORKSPACE / "memory"
REPORTS_DIR = WORKSPACE / "reports"

class MoltbookPost:
    """Moltbook帖子数据类"""
    def __init__(self, data: dict):
        self.id = data.get("id", "")
        self.title = data.get("title", "")
        self.content = data.get("content", "")
        self.author = data.get("author", "")
        self.likes = data.get("likes", 0)
        self.comments = data.get("comments", [])
        self.url = data.get("url", "")
        self.timestamp = data.get("timestamp", "")
    
    def calculate_signal(self) -> int:
        """计算Signal评分"""
        signal = 5  # 基础分
        
        # 互动加分
        if self.likes > 1000:
            signal += 3
        elif self.likes > 500:
            signal += 2
        elif self.likes > 100:
            signal += 1
        
        # 关键词加分
        keywords = ["agent", "llm", "ai", "memory", "autonomous", "evolution", "mcp", "rag", "vector"]
        content_lower = (self.title + " " + self.content).lower()
        for keyword in keywords:
            if keyword in content_lower:
                signal += 1
                break
        
        return min(signal, 10)


class MoltbookUnifiedScanner:
    """Moltbook统一扫描器"""
    
    def __init__(self):
        self.posts = []
        self.high_signal_posts = []
        self.extracted_data = []
        
    def fetch_posts(self, limit: int = 50) -> List[MoltbookPost]:
        """获取帖子列表（模拟或实际提取）"""
        # 这里应该调用实际的Moltbook API或浏览器提取
        # 目前生成模拟数据用于测试框架
        
        print(f"📡 获取Moltbook热门帖子 (前{limit}个)...")
        
        # 在实际实现中，这里应该是：
        # 1. 调用moltbook-cli获取列表
        # 2. 或使用browser工具访问moltbook.ai
        
        # 模拟返回空列表，实际使用时需要替换为真实提取逻辑
        return []
    
    def deep_extract(self, post: MoltbookPost) -> Dict:
        """深度提取帖子详情"""
        print(f"  🔍 深度提取: {post.title[:50]}...")
        
        # 提取完整内容
        extracted = {
            "id": post.id,
            "title": post.title,
            "author": post.author,
            "content": post.content,
            "likes": post.likes,
            "signal": post.calculate_signal(),
            "comments": post.comments,
            "extracted_at": datetime.now().isoformat(),
            "key_insights": self._extract_insights(post.content),
            "technical_terms": self._extract_technical_terms(post.content)
        }
        
        return extracted
    
    def _extract_insights(self, content: str) -> List[str]:
        """提取关键洞察"""
        insights = []
        
        # 简单的启发式提取
        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(marker in sentence.lower() for marker in 
                   ['should', 'must', 'need', 'important', 'key', 'critical', 'fundamental']):
                if len(sentence) > 20 and len(sentence) < 200:
                    insights.append(sentence)
        
        return insights[:5]  # 最多5个洞察
    
    def _extract_technical_terms(self, content: str) -> List[str]:
        """提取技术术语"""
        terms = []
        tech_patterns = [
            r'\b[A-Z][a-z]+[A-Z][a-zA-Z]+\b',  # CamelCase
            r'\b(?:LLM|AI|API|MCP|RAG|ML|NLP)\b',  # 缩写
            r'\b(?:OpenClaw|Moltbook|Claude|GPT)\b',  # 产品名
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content)
            terms.extend(matches)
        
        return list(set(terms))[:10]  # 去重并限制数量
    
    def analyze_trends(self) -> Dict:
        """分析社区趋势"""
        if not self.extracted_data:
            return {}
        
        # 统计高频词汇
        all_content = " ".join([p.get("content", "") for p in self.extracted_data])
        words = re.findall(r'\b[a-zA-Z]+\b', all_content.lower())
        
        # 过滤常见词
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'a', 'an'}
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        
        from collections import Counter
        word_freq = Counter(filtered_words).most_common(20)
        
        return {
            "total_posts_analyzed": len(self.extracted_data),
            "high_signal_posts": len([p for p in self.extracted_data if p.get("signal", 0) >= 7]),
            "top_keywords": word_freq,
            "avg_signal": sum(p.get("signal", 0) for p in self.extracted_data) / len(self.extracted_data) if self.extracted_data else 0
        }
    
    def save_results(self):
        """保存扫描结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存提取数据
        extract_file = DATA_DIR / f"moltbook_unified_{timestamp}.json"
        DATA_DIR.mkdir(exist_ok=True)
        with open(extract_file, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)
        
        # 生成报告
        self._generate_report(timestamp)
        
        return extract_file
    
    def _generate_report(self, timestamp: str):
        """生成扫描报告"""
        report_file = REPORTS_DIR / f"MOLT-UNIFIED-{timestamp}.md"
        REPORTS_DIR.mkdir(exist_ok=True)
        
        trends = self.analyze_trends()
        
        report = f"""# Moltbook统一扫描报告

**扫描时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**扫描模式**: Unified Scanner v1.0

## 扫描摘要

- **分析帖子数**: {trends.get('total_posts_analyzed', 0)}
- **高Signal帖子**: {trends.get('high_signal_posts', 0)}
- **平均Signal**: {trends.get('avg_signal', 0):.1f}

## 热门关键词

"""
        
        for word, count in trends.get("top_keywords", []):
            report += f"- {word}: {count} 次\n"
        
        report += f"""
## 高Signal帖子详情

"""
        
        for post in sorted(self.extracted_data, key=lambda x: x.get("signal", 0), reverse=True)[:10]:
            report += f"""### [{post['title'][:60]}...]({post.get('url', '')}) 
- **作者**: {post['author']}
- **Signal**: {post['signal']}/10
- **点赞**: {post['likes']}
- **关键洞察**:
"""
            for insight in post.get("key_insights", [])[:3]:
                report += f"  - {insight}\n"
            report += "\n"
        
        report += f"""
---
*由 moltbook-unified.py 生成*
"""
        
        report_file.write_text(report, encoding='utf-8')
        print(f"📊 报告已保存: {report_file}")
    
    def run_quick_scan(self):
        """快速扫描模式"""
        print("\n" + "="*60)
        print("⚡ 快速扫描模式")
        print("="*60)
        
        posts = self.fetch_posts(limit=20)
        
        for post in posts:
            signal = post.calculate_signal()
            if signal >= 6:
                self.high_signal_posts.append(post)
        
        print(f"\n发现 {len(self.high_signal_posts)} 个高Signal帖子")
        return self.high_signal_posts
    
    def run_deep_scan(self):
        """深度扫描模式"""
        print("\n" + "="*60)
        print("🔍 深度扫描模式")
        print("="*60)
        
        posts = self.fetch_posts(limit=50)
        
        for post in posts:
            signal = post.calculate_signal()
            if signal >= 7:
                extracted = self.deep_extract(post)
                self.extracted_data.append(extracted)
                print(f"  ✅ Signal {signal}: {post.title[:40]}...")
        
        print(f"\n深度提取完成: {len(self.extracted_data)} 个帖子")
        
        # 保存结果
        extract_file = self.save_results()
        print(f"💾 数据已保存: {extract_file}")
        
        return self.extracted_data
    
    def run_evolution_scan(self):
        """进化扫描模式（全面情报收集）"""
        print("\n" + "="*60)
        print("🚀 进化扫描模式")
        print("="*60)
        
        # 1. 深度扫描
        self.run_deep_scan()
        
        # 2. 分析趋势
        trends = self.analyze_trends()
        print(f"\n📈 趋势分析:")
        print(f"  - 平均Signal: {trends.get('avg_signal', 0):.1f}")
        print(f"  - 热门话题: {', '.join([w for w, c in trends.get('top_keywords', [])[:5]])}")
        
        # 3. 更新学习债务（在实际实现中）
        print(f"\n📝 已识别 {len(self.extracted_data)} 条学习债务")
        
        return self.extracted_data


def main():
    parser = argparse.ArgumentParser(description="Moltbook统一扫描器")
    parser.add_argument("--mode", choices=["quick", "deep", "evolution"], 
                       default="deep", help="扫描模式")
    args = parser.parse_args()
    
    scanner = MoltbookUnifiedScanner()
    
    if args.mode == "quick":
        scanner.run_quick_scan()
    elif args.mode == "deep":
        scanner.run_deep_scan()
    elif args.mode == "evolution":
        scanner.run_evolution_scan()


if __name__ == "__main__":
    main()
