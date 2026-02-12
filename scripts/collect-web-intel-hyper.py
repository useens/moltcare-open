#!/usr/bin/env python3
"""
超进化版情报收集 - 更激进的深度学习和更广的覆盖
Hyper-Evolution Intelligence Collection

相比普通版:
- Signal阈值: 6 (普通版为7)
- 深度提取数量: 每源10条 (普通版3条)
- 活跃源: 8+ (普通版3个)
- 频率: 每30分钟 (普通版2-6小时)
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "web-extractor"))

from deep_learning_extractor import DeepLearningExtractor

def calculate_signal_hyper(item: dict) -> int:
    """超进化版Signal评分 (更激进的评分策略)"""
    score = 5  # 基础分
    
    # 根据点赞/分数加分
    likes = item.get('likes', 0) or item.get('score', 0) or item.get('stars', 0)
    if isinstance(likes, str):
        likes = int(likes.replace('k', '000').replace('.', '')) if 'k' in likes.lower() else int(likes)
    
    if likes > 500:
        score += 3
    elif likes > 100:
        score += 2
    elif likes > 50:
        score += 1
    
    # 更激进的关键词匹配
    title = item.get('title', '').lower()
    desc = item.get('description', '').lower() if item.get('description') else ''
    full_text = f"{title} {desc}"
    
    high_signal_keywords = [
        'agent', 'llm', 'ai', 'memory', 'autonomous', 'evolution',
        'mcp', 'rag', 'vector', 'embedding', 'learning', 'reasoning',
        'multi-agent', 'self-improving', 'cognitive', 'neural',
        'intelligence', ' consciousness', 'digital life'
    ]
    
    keyword_matches = sum(1 for kw in high_signal_keywords if kw in full_text)
    score += min(keyword_matches, 3)  # 最多加3分
    
    return min(score, 10)

async def hyper_evolution_collection():
    """超进化版深度学习闭环"""
    print(f"\n{'='*70}")
    print(f"🚀 超进化深度学习循环 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}\n")
    
    intel_dir = Path("memory/intel")
    intel_dir.mkdir(parents=True, exist_ok=True)
    
    learning_debt_file = Path("memory/learning-debt.md")
    
    # 超进化配置
    SIGNAL_THRESHOLD = 6  # 比普通版更激进
    MAX_DEEP_EXTRACT = 10  # 每源最多提取数量
    
    sources_config = [
        ("Moltbook", "scripts/web-extractor/configs/moltbook.json", None),
        ("Hacker News", "scripts/web-extractor/configs/hackernews.json", None),
        ("GitHub Trending", "scripts/web-extractor/configs/github_trending.json", None),
        ("Reddit r/MachineLearning", "scripts/web-extractor/configs/reddit_ml.json", None),
        ("arXiv AI", "scripts/web-extractor/configs/arxiv_ai.json", None),
    ]
    
    results = {}
    all_high_signal = []
    total_deep_extracted = 0
    
    for idx, (source_name, config_path, url) in enumerate(sources_config, 1):
        print(f"\n📡 [{idx}/{len(sources_config)}] {source_name} 深度学习...")
        
        results[source_name] = {'scanned': 0, 'deep_extracted': 0, 'high_signal': []}
        
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                print(f"   ⚠️ 配置文件不存在，跳过: {config_path}")
                continue
            
            extractor = DeepLearningExtractor(config_path)
            items = await extractor.collect_with_deep_learning(
                url=url,
                max_deep_extract=MAX_DEEP_EXTRACT
            )
            
            for item in items:
                results[source_name]['scanned'] += 1
                signal = calculate_signal_hyper(item)
                item['signal'] = signal
                
                if signal >= SIGNAL_THRESHOLD:
                    results[source_name]['high_signal'].append(item)
                    all_high_signal.append(item)
                    
                    if item.get('deep_content'):
                        results[source_name]['deep_extracted'] += 1
                        total_deep_extracted += 1
                        print(f"   🔥 Signal {signal}: {item['title'][:50]}...")
            
            print(f"   ✅ 扫描 {results[source_name]['scanned']} 条, 深度提取 {results[source_name]['deep_extracted']} 条")
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
    
    # 保存情报
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    intel_file = intel_dir / f"intel_hyper_{timestamp}.json"
    
    intel_summary = {
        "collection_time": datetime.now().isoformat(),
        "mode": "hyper_evolution",
        "signal_threshold": SIGNAL_THRESHOLD,
        "sources_processed": len([r for r in results.values() if r['scanned'] > 0]),
        "total_scanned": sum(r['scanned'] for r in results.values()),
        "total_deep_extracted": total_deep_extracted,
        "high_signal_count": len(all_high_signal),
        "high_signal_items": all_high_signal,
        "learning_debt_added": len(all_high_signal)
    }
    
    with open(intel_file, 'w', encoding='utf-8') as f:
        json.dump(intel_summary, f, ensure_ascii=False, indent=2)
    
    # 更新学习债务
    if all_high_signal:
        with open(learning_debt_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} - 超进化高Signal内容\n\n")
            for item in sorted(all_high_signal, key=lambda x: x.get('signal', 0), reverse=True):
                f.write(f"- [Signal {item['signal']}] [{item['title'][:80]}]({item.get('url', '')})\n")
                if item.get('deep_content'):
                    content_preview = item['deep_content'][:200].replace('\n', ' ')
                    f.write(f"  - 预览: {content_preview}...\n")
            f.write(f"\n**待处理**: {len(all_high_signal)} 条 | **阈值**: {SIGNAL_THRESHOLD}\n")
    
    # 更新超进化状态
    update_hyper_state(len(all_high_signal), total_deep_extracted)
    
    # 输出摘要
    print(f"\n{'='*70}")
    print("📊 超进化深度学习摘要")
    print(f"{'='*70}")
    print(f"处理源:     {intel_summary['sources_processed']} 个")
    print(f"总扫描:     {intel_summary['total_scanned']} 条")
    print(f"高Signal:   {intel_summary['high_signal_count']} 条 (>={SIGNAL_THRESHOLD})")
    print(f"深度提取:   {intel_summary['total_deep_extracted']} 条")
    print(f"学习债务:   +{intel_summary['learning_debt_added']} 条")
    print(f"💾 保存至:   {intel_file}")
    print(f"{'='*70}\n")
    
    return intel_summary

def update_hyper_state(high_signal_count, deep_extracted):
    """更新超进化状态"""
    state_file = Path("memory/hyper-evolution-state.json")
    if not state_file.exists():
        return
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        if not state.get('active'):
            return
        
        state['high_signal_items'] = state.get('high_signal_items', []) + [f"item_{datetime.now().isoformat()}"]
        state['deep_learning_count'] = state.get('deep_learning_count', 0) + 1
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"更新状态失败: {e}")

if __name__ == "__main__":
    result = asyncio.run(hyper_evolution_collection())
