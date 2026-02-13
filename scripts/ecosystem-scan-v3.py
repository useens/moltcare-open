#!/usr/bin/env python3
"""
生态扫描 v3.0 - 深度提取+Playwright整合版
替代原有轻量扫描，实现真正的深度学习闭环
30源并行扫描 + Signal评分 + Playwright深度提取
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent / "web-extractor"))

from deep_learning_extractor import DeepLearningExtractor

# 30源配置 - 整合验证后的可用源
SOURCES = [
    # P0级 - 核心源 (10/10) - 无需API
    {"name": "moltbook", "priority": 10, "enabled": True, 
     "url": "https://www.moltbook.com/?sort=hot",
     "config": "scripts/web-extractor/configs/moltbook.json",
     "max_deep": 3},
    
    {"name": "hackernews", "priority": 10, "enabled": True,
     "url": "https://news.ycombinator.com",
     "config": "scripts/web-extractor/configs/hackernews.json",
     "max_deep": 3},
    
    {"name": "github_trending", "priority": 10, "enabled": True,
     "url": "https://github.com/trending",
     "type": "github",
     "max_deep": 2},
    
    # P1级 - 高价值源 (9/10)
    {"name": "arxiv_ai", "priority": 9, "enabled": True,
     "url": "https://arxiv.org/list/cs.AI/recent",
     "type": "rss",
     "max_deep": 2},
    
    # P2级 - 技术社区 (8/10) - 移除reddit
    {"name": "lobsters", "priority": 8, "enabled": True,
     "url": "https://lobste.rs",
     "type": "feed",
     "max_deep": 2},
    
    {"name": "indiehackers", "priority": 8, "enabled": True,
     "url": "https://indiehackers.com",
     "type": "feed",
     "max_deep": 1},
    
    {"name": "devto_ai", "priority": 8, "enabled": True,
     "url": "https://dev.to/t/ai",
     "type": "feed",
     "max_deep": 2},
    
    # P3级 - 产品/论文 (7/10)
    {"name": "producthunt", "priority": 7, "enabled": True,
     "url": "https://producthunt.com",
     "type": "api",
     "max_deep": 2},
    
    {"name": "papers_with_code", "priority": 7, "enabled": True,
     "url": "https://paperswithcode.com",
     "type": "feed",
     "max_deep": 2},
    
    {"name": "huggingface_papers", "priority": 7, "enabled": True,
     "url": "https://huggingface.co/papers",
     "type": "feed",
     "max_deep": 2},
]


def calculate_signal(item: dict) -> int:
    """计算内容Signal评分 (1-10)"""
    score = 5  # 基础分
    
    # 根据点赞/分数加分
    likes = item.get('likes', 0) or item.get('score', 0) or item.get('stars', 0)
    if isinstance(likes, str):
        likes = int(likes.replace('k', '000').replace('.', '')) if 'k' in likes.lower() else int(likes)
    
    if likes > 1000:
        score += 3
    elif likes > 500:
        score += 2
    elif likes > 100:
        score += 1
    
    # 根据评论数加分
    comments = item.get('comments', 0)
    if isinstance(comments, str):
        comments = int(comments) if comments.isdigit() else 0
    if comments > 50:
        score += 2
    elif comments > 10:
        score += 1
    
    # 根据标题关键词加分
    title = item.get('title', '').lower()
    high_signal_keywords = [
        'agent', 'llm', 'ai', 'memory', 'autonomous', 'evolution',
        'mcp', 'rag', 'vector', 'embedding', 'learning', 'reasoning',
        'multimodal', 'gpt', 'claude', 'deepseek', 'openai'
    ]
    for keyword in high_signal_keywords:
        if keyword in title:
            score += 1
            break
    
    return min(score, 10)


async def scan_source(source: dict) -> dict:
    """扫描单个源"""
    result = {
        'name': source['name'],
        'priority': source['priority'],
        'scanned': 0,
        'deep_extracted': 0,
        'high_signal': [],
        'error': None
    }
    
    if not source['enabled']:
        return result
    
    try:
        print(f"🔍 [{source['name']}] 开始扫描...")
        
        # 使用深度提取器
        if 'config' in source and Path(source['config']).exists():
            extractor = DeepLearningExtractor(source['config'])
            items = await extractor.collect_with_deep_learning(
                url=source.get('url'),
                max_deep_extract=source.get('max_deep', 2)
            )
        else:
            # 使用通用提取器
            extractor = DeepLearningExtractor()
            items = await extractor.extract_from_url(source['url'])
        
        for item in items:
            result['scanned'] += 1
            signal = calculate_signal(item)
            item['signal'] = signal
            
            if signal >= 7:
                result['high_signal'].append(item)
                if item.get('deep_content'):
                    result['deep_extracted'] += 1
        
        print(f"   ✅ {source['name']}: 扫描 {result['scanned']} 条, 高Signal {len(result['high_signal'])} 条, 深度提取 {result['deep_extracted']} 条")
        
    except Exception as e:
        result['error'] = str(e)
        print(f"   ❌ {source['name']}: {e}")
    
    return result


async def ecosystem_scan_v3():
    """生态扫描 v3.0 - 深度提取+Playwright整合"""
    print(f"\n{'='*70}")
    print(f"🌐 生态扫描 v3.0 - 深度提取+Playwright整合")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📡 活跃源: {len([s for s in SOURCES if s['enabled']])} 个")
    print(f"{'='*70}\n")
    
    # 创建报告目录
    report_dir = Path("memory/intel")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # 并发扫描所有源 (最多10个并发)
    tasks = [scan_source(s) for s in SOURCES]
    results = await asyncio.gather(*tasks)
    
    # 统计
    total_scanned = sum(r['scanned'] for r in results)
    total_deep = sum(r['deep_extracted'] for r in results)
    total_high_signal = sum(len(r['high_signal']) for r in results)
    errors = sum(1 for r in results if r['error'])
    
    # 生成报告
    report_file = report_dir / f"ECO-SCAN-{datetime.now().strftime('%Y%m%d-%H%M')}.md"
    
    report_content = f"""# 生态扫描报告 v3.0
**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**扫描引擎**: 深度提取+Playwright整合
**活跃源数**: {len([s for s in SOURCES if s['enabled']])}

## 📊 扫描统计

| 指标 | 数值 |
|------|------|
| 总扫描内容 | {total_scanned} |
| 高Signal内容 | {total_high_signal} |
| 深度提取 | {total_deep} |
| 错误源数 | {errors} |

## 🔍 各源详情

"""
    
    for r in results:
        status_icon = "✅" if not r['error'] else "❌"
        report_content += f"\n### {status_icon} {r['name']} (优先级 {r['priority']}/10)\n"
        report_content += f"- 扫描: {r['scanned']} 条\n"
        report_content += f"- 高Signal: {len(r['high_signal'])} 条\n"
        report_content += f"- 深度提取: {r['deep_extracted']} 条\n"
        if r['error']:
            report_content += f"- 错误: {r['error']}\n"
        
        if r['high_signal']:
            report_content += "- 高Signal内容:\n"
            for item in r['high_signal'][:5]:  # 只显示前5个
                report_content += f"  - Signal {item.get('signal', 0)}: {item.get('title', 'N/A')[:50]}...\n"
    
    report_content += f"\n---\n*生态扫描 v3.0 | 深度提取+Playwright*\n"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # 输出汇总
    print(f"\n{'='*70}")
    print(f"📊 扫描完成")
    print(f"{'='*70}")
    print(f"  总扫描: {total_scanned} 条")
    print(f"  高Signal: {total_high_signal} 条")
    print(f"  深度提取: {total_deep} 条")
    print(f"  错误: {errors} 个源")
    print(f"  报告: {report_file}")
    print(f"{'='*70}\n")
    
    return results


if __name__ == "__main__":
    asyncio.run(ecosystem_scan_v3())
