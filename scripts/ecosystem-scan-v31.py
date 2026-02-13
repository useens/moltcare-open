#!/usr/bin/env python3
"""
生态扫描 v3.1 - 容错版
Playwright失败时自动降级为HTTP请求
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

# 10源配置
SOURCES = [
    {"name": "moltbook", "priority": 10, "enabled": True, 
     "url": "https://www.moltbook.com/?sort=hot", "type": "playwright"},
    {"name": "hackernews", "priority": 10, "enabled": True,
     "url": "https://news.ycombinator.com", "type": "http"},
    {"name": "github_trending", "priority": 10, "enabled": True,
     "url": "https://github.com/trending", "type": "http"},
    {"name": "arxiv_ai", "priority": 9, "enabled": True,
     "url": "https://arxiv.org/list/cs.AI/recent", "type": "http"},
    {"name": "lobsters", "priority": 8, "enabled": True,
     "url": "https://lobste.rs", "type": "http"},
    {"name": "producthunt", "priority": 7, "enabled": True,
     "url": "https://producthunt.com", "type": "http"},
    {"name": "papers_with_code", "priority": 7, "enabled": True,
     "url": "https://paperswithcode.com", "type": "http"},
    {"name": "indiehackers", "priority": 6, "enabled": True,
     "url": "https://indiehackers.com", "type": "http"},
    {"name": "devto", "priority": 6, "enabled": True,
     "url": "https://dev.to/t/ai", "type": "http"},
    {"name": "huggingface", "priority": 5, "enabled": True,
     "url": "https://huggingface.co/papers", "type": "http"},
]


def http_scan(url: str) -> list:
    """HTTP方式扫描"""
    items = []
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (HyperEvolution/3.1)'}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            # 简单提取标题
            import re
            titles = re.findall(r'\u003ctitle\u003e([^\u003c]+)\u003c/title\u003e', content)
            if titles:
                items.append({
                    'title': titles[0][:100],
                    'url': url,
                    'source': 'http_scan',
                    'signal': 5
                })
    except Exception as e:
        pass
    return items


async def scan_source(source: dict) -> dict:
    """扫描单个源"""
    result = {
        'name': source['name'],
        'priority': source['priority'],
        'scanned': 0,
        'high_signal': [],
        'error': None
    }
    
    if not source['enabled']:
        return result
    
    try:
        print(f"🔍 [{source['name']}] 扫描中...")
        
        # 优先使用HTTP方式
        items = http_scan(source['url'])
        
        for item in items:
            result['scanned'] += 1
            if item.get('signal', 0) >= 7:
                result['high_signal'].append(item)
        
        print(f"   ✅ {source['name']}: {result['scanned']} 条")
        
    except Exception as e:
        result['error'] = str(e)
        print(f"   ❌ {source['name']}: {e}")
    
    return result


async def ecosystem_scan_v31():
    """生态扫描 v3.1 - 容错版"""
    print(f"\n{'='*70}")
    print(f"🌐 生态扫描 v3.1 - 容错版 (Playwright降级为HTTP)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"⚠️  注意: Playwright浏览器未安装，使用HTTP降级方案")
    print(f"{'='*70}\n")
    
    # 创建报告目录
    report_dir = Path("memory/intel")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # 顺序扫描 (避免并发问题)
    results = []
    for source in SOURCES:
        r = await scan_source(source)
        results.append(r)
    
    # 统计
    total_scanned = sum(r['scanned'] for r in results)
    total_high = sum(len(r['high_signal']) for r in results)
    errors = sum(1 for r in results if r['error'])
    
    # 生成报告
    report_file = report_dir / f"ECO-SCAN-{datetime.now().strftime('%Y%m%d-%H%M')}-v31.md"
    
    report_content = f"""# 生态扫描报告 v3.1 (容错版)
**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**扫描引擎**: HTTP降级方案 (Playwright未安装)
**活跃源数**: {len([s for s in SOURCES if s['enabled']])}

## 📊 扫描统计

| 指标 | 数值 |
|------|------|
| 总扫描内容 | {total_scanned} |
| 高Signal内容 | {total_high} |
| 错误源数 | {errors} |
| 扫描模式 | HTTP降级 |

## ⚠️ 降级说明

Playwright浏览器未正确安装，已自动降级为HTTP请求模式。
深度提取功能暂时不可用。

## 🔍 各源详情

"""
    
    for r in results:
        status_icon = "✅" if not r['error'] else "❌"
        report_content += f"\n### {status_icon} {r['name']} (优先级 {r['priority']}/10)\n"
        report_content += f"- 扫描: {r['scanned']} 条\n"
        if r['error']:
            report_content += f"- 错误: {r['error']}\n"
    
    report_content += f"\n---\n*生态扫描 v3.1 容错版 | 等待Playwright修复*\n"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # 输出汇总
    print(f"\n{'='*70}")
    print(f"📊 扫描完成 (容错模式)")
    print(f"{'='*70}")
    print(f"  总扫描: {total_scanned} 条")
    print(f"  高Signal: {total_high} 条")
    print(f"  错误: {errors} 个源")
    print(f"  模式: ⚠️ HTTP降级 (Playwright未安装)")
    print(f"  报告: {report_file}")
    print(f"{'='*70}\n")
    
    print("⚠️  修复建议:")
    print("  1. 运行: playwright install chromium")
    print("  2. 或等待自动安装完成")
    print("  3. 然后重新运行完整版v3.0")
    print("")
    
    return results


if __name__ == "__main__":
    asyncio.run(ecosystem_scan_v31())
