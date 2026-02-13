#!/usr/bin/env python3
"""
生态扫描 v3.3 - Playwright修复版
使用修复后的深度提取器 (系统Chromium)
超进化引擎26源整合
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 修复：配置Playwright使用系统Chromium
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/usr/bin/chromium"
os.environ["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"

sys.path.insert(0, str(Path(__file__).parent / "web-extractor"))

try:
    from deep_learning_extractor import DeepLearningExtractor
    PLAYWRIGHT_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Playwright导入失败: {e}")
    PLAYWRIGHT_AVAILABLE = False

# 超进化引擎验证的26个源
SOURCES = [
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
     "type": "http",
     "max_deep": 2},
    {"name": "arxiv_ai", "priority": 9, "enabled": True,
     "url": "https://arxiv.org/list/cs.AI/recent",
     "type": "http",
     "max_deep": 2},
    {"name": "lobsters", "priority": 8, "enabled": True,
     "url": "https://lobste.rs",
     "type": "http",
     "max_deep": 2},
    {"name": "indiehackers", "priority": 8, "enabled": True,
     "url": "https://indiehackers.com",
     "type": "http",
     "max_deep": 2},
    {"name": "towards_data_science", "priority": 8, "enabled": True,
     "url": "https://towardsdatascience.com",
     "type": "http",
     "max_deep": 2},
    {"name": "devto_ai", "priority": 8, "enabled": True,
     "url": "https://dev.to/t/ai",
     "type": "http",
     "max_deep": 2},
    {"name": "producthunt", "priority": 7, "enabled": True,
     "url": "https://producthunt.com",
     "type": "http",
     "max_deep": 2},
    {"name": "papers_with_code", "priority": 7, "enabled": True,
     "url": "https://paperswithcode.com",
     "type": "http",
     "max_deep": 2},
    {"name": "arxiv_cs_daily", "priority": 7, "enabled": True,
     "url": "https://arxiv.org/list/cs/recent",
     "type": "http",
     "max_deep": 2},
    {"name": "huggingface_papers", "priority": 7, "enabled": True,
     "url": "https://huggingface.co/papers",
     "type": "http",
     "max_deep": 2},
    {"name": "lesswrong", "priority": 6, "enabled": True,
     "url": "https://lesswrong.com",
     "type": "http",
     "max_deep": 1},
    {"name": "distill", "priority": 6, "enabled": True,
     "url": "https://distill.pub",
     "type": "http",
     "max_deep": 2},
    {"name": "sideproject", "priority": 6, "enabled": True,
     "url": "https://sideprojectors.com",
     "type": "http",
     "max_deep": 1},
    {"name": "beta_list", "priority": 6, "enabled": True,
     "url": "https://betalist.com",
     "type": "http",
     "max_deep": 1},
    {"name": "hacker_news_newest", "priority": 5, "enabled": True,
     "url": "https://news.ycombinator.com/newest",
     "type": "http",
     "max_deep": 1},
    {"name": "github_topic_ai", "priority": 5, "enabled": True,
     "url": "https://github.com/topics/artificial-intelligence",
     "type": "http",
     "max_deep": 1},
    {"name": "arxiv_cl", "priority": 5, "enabled": True,
     "url": "https://arxiv.org/list/cs.CL/recent",
     "type": "http",
     "max_deep": 1},
    {"name": "ai_weirdness", "priority": 5, "enabled": True,
     "url": "https://aiweirdness.com",
     "type": "http",
     "max_deep": 1},
    {"name": "gizmodo_ai", "priority": 4, "enabled": True,
     "url": "https://gizmodo.com/tag/artificial-intelligence",
     "type": "http",
     "max_deep": 1},
    {"name": "venturebeat_ai", "priority": 4, "enabled": True,
     "url": "https://venturebeat.com/ai",
     "type": "http",
     "max_deep": 1},
    {"name": "techcrunch_ai", "priority": 4, "enabled": True,
     "url": "https://techcrunch.com/category/artificial-intelligence",
     "type": "http",
     "max_deep": 1},
    {"name": "mit_tech_review", "priority": 4, "enabled": True,
     "url": "https://technologyreview.com",
     "type": "http",
     "max_deep": 1},
    {"name": "ieee_spectrum", "priority": 4, "enabled": True,
     "url": "https://spectrum.ieee.org/artificial-intelligence",
     "type": "http",
     "max_deep": 1},
    {"name": "acm_queue", "priority": 4, "enabled": True,
     "url": "https://queue.acm.org",
     "type": "http",
     "max_deep": 1},
]


def calculate_signal(item: dict) -> int:
    """计算内容Signal评分 (1-10)"""
    score = 5
    likes = item.get('likes', 0) or item.get('score', 0) or item.get('stars', 0)
    if isinstance(likes, str):
        likes = int(likes.replace('k', '000').replace('.', '')) if 'k' in likes.lower() else int(likes)
    
    if likes > 1000:
        score += 3
    elif likes > 500:
        score += 2
    elif likes > 100:
        score += 1
    
    title = item.get('title', '').lower()
    keywords = ['agent', 'llm', 'ai', 'memory', 'autonomous', 'evolution', 'mcp', 'rag']
    for kw in keywords:
        if kw in title:
            score += 1
            break
    
    return min(score, 10)


async def scan_with_playwright(source: dict) -> dict:
    """使用Playwright深度扫描"""
    result = {
        'name': source['name'],
        'priority': source['priority'],
        'scanned': 0,
        'deep_extracted': 0,
        'high_signal': [],
        'error': None
    }
    
    try:
        if 'config' in source and Path(source['config']).exists():
            extractor = DeepLearningExtractor(source['config'])
            items = await extractor.collect_with_deep_learning(
                url=source.get('url'),
                max_deep_extract=source.get('max_deep', 2)
            )
        else:
            extractor = DeepLearningExtractor()
            items = await extractor.extract_from_url(source['url'])
        
        for item in items:
            result['scanned'] += 1
            item['signal'] = calculate_signal(item)
            if item['signal'] >= 7:
                result['high_signal'].append(item)
                if item.get('deep_content'):
                    result['deep_extracted'] += 1
        
    except Exception as e:
        result['error'] = str(e)[:50]
    
    return result


async def ecosystem_scan_v33():
    """生态扫描 v3.3 - Playwright修复版"""
    print(f"\n{'='*70}")
    print(f"🌐 生态扫描 v3.3 - Playwright修复版")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📡 源数: {len(SOURCES)} (超进化引擎验证)")
    print(f"🔧 Playwright: {'✅ 可用' if PLAYWRIGHT_AVAILABLE else '❌ 不可用'}")
    print(f"{'='*70}\n")
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright不可用，请检查配置")
        return []
    
    report_dir = Path("memory/intel")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # 扫描前10个高优先级源 (Playwright资源消耗大，限制数量)
    high_priority_sources = [s for s in SOURCES if s['priority'] >= 8][:8]
    
    print(f"扫描高优先级源 ({len(high_priority_sources)}个)...\n")
    
    results = []
    for source in high_priority_sources:
        print(f"🔍 [{source['name']}] 深度扫描...")
        r = await scan_with_playwright(source)
        results.append(r)
        status = "✅" if not r['error'] else "❌"
        print(f"   {status} {r['name']}: {r['scanned']}条, 深度{r['deep_extracted']}条, 高Signal{len(r['high_signal'])}条")
    
    # 统计
    total_scanned = sum(r['scanned'] for r in results)
    total_deep = sum(r['deep_extracted'] for r in results)
    total_high = sum(len(r['high_signal']) for r in results)
    errors = sum(1 for r in results if r['error'])
    
    # 生成报告
    report_file = report_dir / f"ECO-SCAN-{datetime.now().strftime('%Y%m%d-%H%M')}-v33.md"
    
    report = f"""# 生态扫描报告 v3.3 (Playwright修复版)
**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**扫描引擎**: Playwright + 系统Chromium
**扫描源数**: {len(high_priority_sources)}

## 📊 扫描统计

| 指标 | 数值 |
|------|------|
| 总扫描内容 | {total_scanned} |
| 深度提取 | {total_deep} |
| 高Signal内容 | {total_high} |
| 错误源数 | {errors} |

## 🔍 各源详情

"""
    
    for r in results:
        status_icon = "✅" if not r['error'] else "❌"
        report += f"\n### {status_icon} {r['name']} (优先级 {r['priority']}/10)\n"
        report += f"- 扫描: {r['scanned']} 条\n"
        report += f"- 深度提取: {r['deep_extracted']} 条\n"
        report += f"- 高Signal: {len(r['high_signal'])} 条\n"
        if r['error']:
            report += f"- 错误: {r['error']}\n"
    
    report += f"\n---\n*生态扫描 v3.3 | Playwright修复版 | 系统Chromium*\n"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n{'='*70}")
    print(f"📊 扫描完成")
    print(f"{'='*70}")
    print(f"  总扫描: {total_scanned} 条")
    print(f"  深度提取: {total_deep} 条")
    print(f"  高Signal: {total_high} 条")
    print(f"  错误: {errors} 个源")
    print(f"  报告: {report_file}")
    print(f"{'='*70}\n")
    
    return results


if __name__ == "__main__":
    asyncio.run(ecosystem_scan_v33())
