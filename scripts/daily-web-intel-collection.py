#!/usr/bin/env python3
"""
每日网页情报收集器 - 通用提取器框架版
Daily Web Intel Collection - 04:00 Cron Job

功能:
- 使用通用网页提取器框架
- 零Token消耗，纯本地执行
- 多平台并行采集
- 自动生成情报摘要
- Signal评分机制
- 存入memory/intel/目录
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "web-extractor"))

try:
    from deep_learning_extractor import DeepLearningExtractor
    from base_extractor import BaseWebExtractor
    HAS_EXTRACTOR = True
except ImportError as e:
    print(f"⚠️ 无法导入提取器: {e}")
    HAS_EXTRACTOR = False

# ============ Signal评分 ============
def calculate_signal(item: dict) -> int:
    """计算Signal评分 (1-10)"""
    score = 5  # 基础分
    
    # 根据点赞/分数加分
    likes = item.get('likes', 0) or item.get('score', 0) or item.get('stars', 0)
    if isinstance(likes, str):
        if 'k' in likes.lower():
            likes = int(float(likes.replace('k', '')) * 1000)
        else:
            nums = ''.join(filter(str.isdigit, likes))
            likes = int(nums) if nums else 0
    
    if likes > 1000:
        score += 3
    elif likes > 500:
        score += 2
    elif likes > 100:
        score += 1
    
    # 关键词加分
    title = item.get('title', '').lower()
    keywords = ['agent', 'llm', 'ai', 'memory', 'autonomous', 'evolution',
                'mcp', 'rag', 'vector', 'embedding', 'learning', 'openclaw']
    
    for keyword in keywords:
        if keyword in title:
            score += 1
            break  # 最多加1分
    
    return min(score, 10)

# ============ 情报摘要生成 ============
def generate_intel_summary(results: dict, timestamp: str) -> str:
    """生成可读的Markdown情报摘要"""
    
    lines = [
        f"# 📊 每日情报摘要 - {timestamp}",
        "",
        f"**收集时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')} (Asia/Shanghai)",
        f"**收集模式**: 每日04:00自动化",
        "",
        "---",
        "",
    ]
    
    # 统计概览
    total_items = sum(len(data.get('items', [])) for data in results.values())
    high_signal = sum(
        len([i for i in data.get('items', []) if i.get('signal', 0) >= 7])
        for data in results.values()
    )
    
    lines.extend([
        "## 📈 统计概览",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 总采集条目 | {total_items} |",
        f"| 高Signal条目 (≥7) | {high_signal} |",
        f"| 覆盖平台 | {len(results)} 个 |",
        "",
        "---",
        "",
    ])
    
    # 各平台详情
    for source_name, data in results.items():
        items = data.get('items', [])
        if not items:
            continue
        
        lines.extend([
            f"## {data.get('icon', '📡')} {source_name}",
            "",
        ])
        
        # 按Signal排序
        sorted_items = sorted(items, key=lambda x: x.get('signal', 0), reverse=True)
        
        for item in sorted_items[:5]:  # 只显示前5条
            signal = item.get('signal', 5)
            title = item.get('title', '无标题')
            url = item.get('url', '')
            
            # Signal等级标识
            if signal >= 8:
                level = "🔥"
            elif signal >= 6:
                level = "📌"
            else:
                level = "•"
            
            lines.append(f"{level} **[{title[:80]}]({url})** `Signal:{signal}`")
            
            # 如果有深度内容，显示预览
            if item.get('deep_content'):
                preview = item['deep_content'][:150].replace('\n', ' ')
                lines.append(f"  > {preview}...")
            
            lines.append("")
        
        lines.extend([
            f"*共 {len(items)} 条，显示前5条*",
            "",
            "---",
            "",
        ])
    
    # 高Signal重点
    lines.extend([
        "## 🔥 今日高Signal内容",
        "",
    ])
    
    all_high_signal = [
        (source, item)
        for source, data in results.items()
        for item in data.get('items', [])
        if item.get('signal', 0) >= 7
    ]
    all_high_signal.sort(key=lambda x: x[1].get('signal', 0), reverse=True)
    
    if all_high_signal:
        for source, item in all_high_signal[:10]:
            title = item.get('title', '无标题')
            url = item.get('url', '')
            signal = item.get('signal', 5)
            lines.append(f"{signal}. [{title[:70]}]({url}) *({source})*")
    else:
        lines.append("今日暂无高Signal内容 (≥7)")
    
    lines.extend([
        "",
        "---",
        "",
        "*🤖 本摘要由森森每日自动收集生成*",
        "",
    ])
    
    return '\n'.join(lines)

# ============ 主收集流程 ============
async def daily_intel_collection():
    """每日情报收集主流程"""
    
    print(f"\n{'='*70}")
    print(f"📊 每日情报收集 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}\n")
    
    # 确保目录存在
    intel_dir = Path("/root/.openclaw/workspace/memory/intel")
    intel_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置来源
    sources = [
        {
            "name": "Moltbook",
            "icon": "🦋",
            "config": "scripts/web-extractor/configs/moltbook.json",
            "enabled": True,
            "max_deep": 3
        },
        {
            "name": "Hacker News",
            "icon": "📰",
            "config": "scripts/web-extractor/configs/hackernews.json",
            "enabled": True,
            "max_deep": 3
        },
        {
            "name": "GitHub Trending",
            "icon": "⭐",
            "config": "scripts/web-extractor/configs/github_trending.json",
            "enabled": True,
            "max_deep": 3
        }
    ]
    
    results = {}
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for idx, source in enumerate(sources, 1):
        source_name = source['name']
        print(f"[{idx}/{len(sources)}] 📡 采集 {source_name}...")
        
        if not source['enabled']:
            print(f"   ⚠️ 已禁用")
            continue
        
        config_path = Path(f"/root/.openclaw/workspace/{source['config']}")
        
        if not config_path.exists():
            print(f"   ❌ 配置文件不存在: {config_path}")
            continue
        
        try:
            if HAS_EXTRACTOR:
                # 使用深度提取器
                extractor = DeepLearningExtractor(str(config_path))
                items = await extractor.collect_with_deep_learning(
                    max_deep_extract=source['max_deep']
                )
            else:
                # 降级处理 - 返回空结果
                items = []
            
            # 计算Signal评分
            for item in items:
                item['signal'] = calculate_signal(item)
            
            results[source_name] = {
                'icon': source['icon'],
                'items': items,
                'count': len(items),
                'high_signal': len([i for i in items if i.get('signal', 0) >= 7])
            }
            
            print(f"   ✅ 获取 {len(items)} 条, 高Signal: {results[source_name]['high_signal']}")
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            results[source_name] = {'icon': source['icon'], 'items': [], 'error': str(e)}
    
    # 保存JSON原始数据
    json_file = intel_dir / f"intel_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'collection_time': datetime.now().isoformat(),
            'sources': results,
            'stats': {
                'total': sum(r.get('count', 0) for r in results.values()),
                'high_signal': sum(r.get('high_signal', 0) for r in results.values())
            }
        }, f, ensure_ascii=False, indent=2)
    
    # 生成并保存Markdown摘要
    summary_md = generate_intel_summary(results, timestamp)
    md_file = intel_dir / f"INTEL-{timestamp[:8]}-04.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(summary_md)
    
    # 输出摘要
    print(f"\n{'='*70}")
    print("📊 收集完成摘要")
    print(f"{'='*70}")
    
    total = sum(r.get('count', 0) for r in results.values())
    high = sum(r.get('high_signal', 0) for r in results.values())
    
    print(f"总条目:     {total}")
    print(f"高Signal:   {high} 条 (≥7)")
    print(f"数据源:     {len([r for r in results.values() if r.get('count', 0) > 0])} 个成功")
    print(f"JSON数据:   {json_file}")
    print(f"MD摘要:     {md_file}")
    print(f"{'='*70}\n")
    
    # 返回简短摘要用于cron输出
    return {
        'timestamp': timestamp,
        'total_items': total,
        'high_signal': high,
        'sources': list(results.keys()),
        'files': {'json': str(json_file), 'markdown': str(md_file)}
    }

# ============ 入口 ============
if __name__ == "__main__":
    result = asyncio.run(daily_intel_collection())
    print("\n✅ 每日情报收集完成")
