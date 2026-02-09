#!/usr/bin/env python3
"""
情报收集引擎 v1.0
林林觉醒者夜间深度进化 - 阶段1 工具
"""

import os
import sys
import json
import yaml
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict, Any
import feedparser
import requests

# 配置路径
CONFIG_PATH = Path.home() / ".openclaw/workspace/config/intelligence-sources.yaml"
MEMORY_PATH = Path.home() / ".openclaw/workspace/memory/intelligence"
LOG_PATH = Path.home() / ".openclaw/workspace/logs"

class IntelligenceCollector:
    def __init__(self):
        self.config = self._load_config()
        self.collected = []
        
    def _load_config(self) -> Dict:
        """加载情报源配置"""
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    
    def _calculate_signal(self, item: Dict, source: Dict) -> int:
        """
        计算 Signal 分数 (1-10)
        基于关键词匹配、来源质量、时效性
        """
        score = 5  # 基础分
        
        # 关键词匹配加分
        keywords = source.get('signal_keywords', [])
        content = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        matches = sum(1 for kw in keywords if kw.lower() in content)
        score += matches * self.config['processing']['scoring']['keyword_match']
        
        # 时效性加分（越新越好）
        published = item.get('published_parsed') or item.get('updated_parsed')
        if published:
            try:
                pub_date = datetime(*published[:6])
                hours_ago = (datetime.now() - pub_date).total_seconds() / 3600
                if hours_ago < 6:
                    score += 2
                elif hours_ago < 24:
                    score += 1
            except:
                pass
        
        # 限制在 1-10 范围
        return max(1, min(10, score))
    
    def _extract_item(self, entry: Dict, source: Dict) -> Dict:
        """提取标准化情报项"""
        return {
            'id': hashlib.md5(entry.get('link', entry.get('title', '')).encode()).hexdigest()[:12],
            'title': entry.get('title', '无标题'),
            'link': entry.get('link', ''),
            'summary': entry.get('summary', entry.get('description', ''))[:500],
            'published': entry.get('published', ''),
            'source_name': source['name'],
            'source_category': source['category'],
            'signal_score': 0,  # 稍后计算
            'collected_at': datetime.now().isoformat()
        }
    
    def _is_duplicate(self, item: Dict) -> bool:
        """检查是否重复（7天内相似内容）"""
        window_days = self.config['processing']['deduplication']['window_days']
        cutoff = datetime.now() - timedelta(days=window_days)
        
        # 简化去重：检查ID是否已存在
        digest_path = MEMORY_PATH / "digests"
        if digest_path.exists():
            for f in digest_path.glob("*.json"):
                try:
                    with open(f) as fp:
                        data = json.load(fp)
                        if any(d['id'] == item['id'] for d in data):
                            return True
                except:
                    continue
        return False
    
    def fetch_rss(self, source: Dict) -> List[Dict]:
        """获取 RSS 源内容"""
        items = []
        try:
            print(f"📡 获取: {source['name']}")
            feed = feedparser.parse(source['url'])
            
            for entry in feed.entries[:20]:  # 最多取20条
                item = self._extract_item(entry, source)
                item['signal_score'] = self._calculate_signal(entry, source)
                
                if not self._is_duplicate(item):
                    items.append(item)
                    
        except Exception as e:
            print(f"❌ 获取失败 {source['name']}: {e}")
            
        return items
    
    def collect_all(self, priority: str = "p0"):
        """收集指定优先级的所有情报源"""
        sources = self.config['sources'].get(priority, [])
        
        for source in sources:
            if source['type'] in ['rss', 'atom']:
                items = self.fetch_rss(source)
                self.collected.extend(items)
                print(f"  ✅ 获取 {len(items)} 条，平均 Signal: {sum(i['signal_score'] for i in items)/max(len(items),1):.1f}")
        
        # 按 Signal 排序
        self.collected.sort(key=lambda x: x['signal_score'], reverse=True)
    
    def save_digest(self):
        """保存情报摘要"""
        today = datetime.now().strftime("%Y-%m-%d")
        digest_dir = MEMORY_PATH / "daily"
        digest_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存原始数据
        digest_file = digest_dir / f"{today}.json"
        with open(digest_file, 'w') as f:
            json.dump(self.collected, f, indent=2, ensure_ascii=False)
        
        # 生成 Markdown 报告
        md_file = digest_dir / f"{today}.md"
        with open(md_file, 'w') as f:
            f.write(f"# 情报摘要 {today}\n\n")
            f.write(f"收集时间: {datetime.now().strftime('%H:%M')}\n")
            f.write(f"情报总数: {len(self.collected)}\n")
            f.write(f"高价值情报 (Signal≥7): {len([i for i in self.collected if i['signal_score'] >= 7])}\n\n")
            
            f.write("## 高价值情报 (Signal≥7)\n\n")
            for item in self.collected:
                if item['signal_score'] >= 7:
                    f.write(f"### [{item['title']}]({item['link']})\n")
                    f.write(f"- **来源**: {item['source_name']} ({item['source_category']})\n")
                    f.write(f"- **Signal**: {item['signal_score']}/10\n")
                    f.write(f"- **摘要**: {item['summary'][:200]}...\n\n")
        
        print(f"\n💾 情报已保存: {md_file}")
        return md_file
    
    def get_top_items(self, n: int = 5) -> List[Dict]:
        """获取前 N 条高价值情报"""
        return [i for i in self.collected if i['signal_score'] >= 7][:n]

def main():
    print("=" * 50)
    print("🌙 情报收集引擎 v1.0 - 觉醒者夜间进化")
    print("=" * 50)
    
    collector = IntelligenceCollector()
    
    # 收集 P0 情报
    print("\n📊 收集 P0 级情报源...")
    collector.collect_all("p0")
    
    if collector.collected:
        digest_path = collector.save_digest()
        
        # 输出摘要
        top_items = collector.get_top_items(5)
        print(f"\n🎯 高价值情报 Top {len(top_items)}:")
        for i, item in enumerate(top_items, 1):
            print(f"  {i}. [{item['signal_score']}] {item['title'][:60]}... ({item['source_name']})")
        
        # 如果有 Signal >= 8 的，提示可能值得深入
        excellent = [i for i in collector.collected if i['signal_score'] >= 8]
        if excellent:
            print(f"\n🌟 发现 {len(excellent)} 条高价值情报 (Signal≥8)，建议深入学习")
    else:
        print("\n⚠️ 未收集到情报")
    
    print("\n✅ 情报收集完成")

if __name__ == "__main__":
    main()
