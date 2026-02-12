#!/usr/bin/env python3
"""
超进化引擎 v2.0 - 12源并行扫描框架
Phase 2: 真实扫描 + 并行执行 + 产出情报
"""

import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import psutil

sys.path.insert(0, str(Path(__file__).parent / "web-extractor"))

CONFIG = {
    "version": "2.0.0",
    "codename": "HyperEngine-Parallel",
    "cpu_target": 70,
    "memory_target_mb": 6144,
    "scan_interval": 600,
    "max_workers": 6,
    "signal_threshold": 6,
}

# 6个信息源配置（Phase 2先实现6个，Phase 3扩展到12个）
SOURCES = [
    {"name": "moltbook", "priority": 10, "enabled": True},
    {"name": "hackernews", "priority": 10, "enabled": True},
    {"name": "github_trending", "priority": 10, "enabled": True},
    {"name": "lobsters", "priority": 6, "enabled": True},
    {"name": "producthunt", "priority": 6, "enabled": True},
    {"name": "devto", "priority": 6, "enabled": False},
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_stats():
    return {
        "cpu": psutil.cpu_percent(interval=0.5),
        "mem_mb": psutil.virtual_memory().used / 1024 / 1024,
        "mem_percent": psutil.virtual_memory().percent,
    }

async def scan_with_extractor(source_name: str, config_path: str) -> List[Dict]:
    """使用深度提取器扫描单个源"""
    try:
        from deep_learning_extractor import DeepLearningExtractor
        
        extractor = DeepLearningExtractor(config_path)
        items = await extractor.collect_with_deep_learning(max_deep_extract=3)
        
        # 添加来源标记
        for item in items:
            item['source'] = source_name
            item['collected_at'] = datetime.now().isoformat()
        
        return items
    except Exception as e:
        log(f"  ❌ {source_name}: 提取错误 - {e}")
        return []

def scan_source_worker(source: Dict) -> Dict:
    """扫描单个源（工作函数）"""
    name = source["name"]
    
    config_map = {
        "moltbook": "scripts/web-extractor/configs/moltbook.json",
        "hackernews": "scripts/web-extractor/configs/hackernews.json",
        "github_trending": "scripts/web-extractor/configs/github_trending.json",
        "lobsters": "scripts/web-extractor/configs/lobsters.json",
        "producthunt": "scripts/web-extractor/configs/producthunt.json",
    }
    
    config_path = config_map.get(name)
    
    try:
        if not config_path or not os.path.exists(config_path):
            return {
                "source": name,
                "status": "no_config",
                "items": [],
                "count": 0,
            }
        
        start_time = time.time()
        
        # 使用asyncio运行提取器
        items = asyncio.run(scan_with_extractor(name, config_path))
        
        elapsed = time.time() - start_time
        
        # 计算Signal
        high_signal_items = []
        for item in items:
            signal = calculate_signal(item)
            item['signal'] = signal
            if signal >= CONFIG['signal_threshold']:
                high_signal_items.append(item)
        
        return {
            "source": name,
            "status": "success" if items else "no_items",
            "items": high_signal_items,
            "count": len(high_signal_items),
            "elapsed": elapsed,
            "priority": source["priority"]
        }
        
    except Exception as e:
        log(f"  ❌ {name}: 异常 - {e}")
        return {
            "source": name,
            "status": "error",
            "items": [],
            "count": 0,
            "error": str(e)
        }

def calculate_signal(item: dict) -> int:
    """计算Signal评分"""
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
    keywords = ['agent', 'llm', 'ai', 'memory', 'autonomous', 'evolution',
                'mcp', 'rag', 'vector', 'embedding', 'learning']
    if any(kw in title for kw in keywords):
        score += 1
    
    return min(score, 10)

def save_intelligence(results: List[Dict]):
    """保存情报到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    intel_dir = Path("/root/.openclaw/workspace/memory/intel")
    intel_dir.mkdir(parents=True, exist_ok=True)
    
    all_items = []
    for r in results:
        if r.get("items"):
            all_items.extend(r["items"])
    
    if not all_items:
        log("⚠️ 本轮无高Signal内容")
        return 0
    
    intel_file = intel_dir / f"intel_hyper_{timestamp}.json"
    intel_data = {
        "timestamp": datetime.now().isoformat(),
        "version": CONFIG["version"],
        "total_items": len(all_items),
        "items": all_items
    }
    
    with open(intel_file, 'w', encoding='utf-8') as f:
        json.dump(intel_data, f, indent=2, default=str)
    
    update_learning_debt(all_items)
    
    log(f"✅ 保存 {len(all_items)} 条高Signal内容到 {intel_file.name}")
    return len(all_items)

def update_learning_debt(items: List[Dict]):
    """更新学习债务"""
    debt_file = Path("/root/.openclaw/workspace/memory/learning-debt.md")
    
    debt_entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} - 超进化扫描\n\n"
    debt_entry += "| 日期 | 来源 | URL | Signal | 主题 | 发现时状态 | 截止时间 | 状态 | 完成时间 |\n"
    debt_entry += "|------|------|-----|--------|------|-----------|---------|------|---------|\n"
    
    for item in items[:10]:
        signal = item.get('signal', 5)
        title = item.get('title', 'Unknown')[:50]
        url = item.get('url', '')
        source = item.get('source', 'unknown')
        deadline = datetime.now().strftime('%Y-%m-%d %H:%M')
        debt_entry += f"| {datetime.now().strftime('%Y-%m-%d')} | {source} | {url} | {signal} | {title} | 超进化v2 | {deadline} | 待处理 | - |\n"
    
    if debt_file.exists():
        with open(debt_file, 'a', encoding='utf-8') as f:
            f.write(debt_entry)
    
    log(f"📝 更新学习债务: {len(items)} 条")

def run_parallel_scan() -> List[Dict]:
    """并行扫描所有启用的源"""
    enabled_sources = [s for s in SOURCES if s["enabled"]]
    log(f"🔥 启动 {len(enabled_sources)}/{len(SOURCES)} 源并行扫描...")
    
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
        futures = {executor.submit(scan_source_worker, s): s for s in enabled_sources}
        
        for future in futures:
            try:
                result = future.result(timeout=300)
                results.append(result)
                status_icon = "✅" if result["status"] == "success" else "⚠️"
                log(f"  {status_icon} {result['source']}: {result.get('count', 0)} 条 ({result['status']})")
            except Exception as e:
                source = futures[future]
                log(f"  ❌ {source['name']}: 超时 - {e}")
                results.append({
                    "source": source["name"],
                    "status": "timeout",
                    "error": str(e),
                    "count": 0
                })
    
    elapsed = time.time() - start_time
    log(f"⏱️ 扫描完成: {len(results)} 源, 耗时 {elapsed:.1f}s")
    
    return results

def main_loop():
    """主循环"""
    log(f"🚀 超进化引擎 v{CONFIG['version']} 启动")
    log(f"📊 配置: {len([s for s in SOURCES if s['enabled']])} 源并行, Signal≥{CONFIG['signal_threshold']}")
    
    cycle = 0
    while True:
        cycle += 1
        start_time = time.time()
        
        log(f"\n{'='*60}")
        log(f"🔥 第 {cycle} 轮扫描 - {datetime.now().strftime('%H:%M:%S')}")
        log(f"{'='*60}")
        
        # 1. 并行扫描
        results = run_parallel_scan()
        
        # 2. 保存情报
        total_found = save_intelligence(results)
        
        # 3. 统计
        success_count = sum(1 for r in results if r["status"] == "success")
        stats = get_stats()
        
        log(f"\n📈 本轮统计:")
        log(f"   成功率: {success_count}/{len(results)} 源")
        log(f"   高Signal: {total_found} 条")
        log(f"   CPU: {stats['cpu']:.1f}% | 内存: {stats['mem_mb']:.0f}MB")
        
        # 4. 等待下一轮
        elapsed = time.time() - start_time
        sleep_time = max(10, CONFIG["scan_interval"] - elapsed)
        log(f"\n⏳ 等待 {sleep_time:.0f}s 后开始下一轮...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log("\n🛑 用户中断")
    except Exception as e:
        log(f"\n💥 引擎异常: {e}")
        import traceback
        traceback.print_exc()
        raise
