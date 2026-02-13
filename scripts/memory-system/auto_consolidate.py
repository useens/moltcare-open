#!/usr/bin/env python3
"""
自动记忆整理脚本 - 每日执行
功能：
1. 整理daily文件，提取重要内容到长期记忆
2. 归档过期短期记忆
3. 构建记忆关联图谱
4. 清理临时记忆
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from layered_memory import get_memory_system, MemoryEntry

# 路径配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
DAILY_DIR = MEMORY_DIR / "daily"
ARCHIVE_DIR = MEMORY_DIR / "archive"
LOG_FILE = WORKSPACE / "logs/memory/consolidation.log"

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    # 写入日志文件
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_msg + '\n')


def consolidate_daily_files():
    """整理所有daily文件"""
    ms = get_memory_system()
    
    log("=" * 60)
    log("开始整理每日记忆")
    log("=" * 60)
    
    total_extracted = 0
    
    # 处理最近7天的daily文件
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        count = ms.consolidate_daily_memories(date_str)
        if count > 0:
            log(f"  {date_str}: 提取 {count} 条记忆")
            total_extracted += count
    
    log(f"总计提取: {total_extracted} 条记忆")
    return total_extracted


def archive_old_short_term():
    """归档旧的短期记忆到长期记忆"""
    log("归档短期记忆...")
    
    short_term_file = MEMORY_DIR / "temp/short_term.json"
    if not short_term_file.exists():
        log("  短期记忆文件不存在")
        return 0
    
    with open(short_term_file, 'r', encoding='utf-8') as f:
        memories = json.load(f)
    
    archived = 0
    remaining = []
    
    for m in memories:
        created = datetime.fromisoformat(m["created_at"])
        age_days = (datetime.now() - created).days
        
        # 7天以上的高重要性记忆归档到长期
        if age_days > 7 and m["importance"] >= 7:
            ms = get_memory_system()
            ms._archive_to_long_term(MemoryEntry.from_dict(m))
            archived += 1
        else:
            remaining.append(m)
    
    # 保存剩余的记忆
    with open(short_term_file, 'w', encoding='utf-8') as f:
        json.dump(remaining, f, ensure_ascii=False, indent=2)
    
    log(f"  归档 {archived} 条到长期记忆")
    log(f"  剩余 {len(remaining)} 条在短期记忆")
    return archived


def build_memory_associations():
    """自动构建记忆关联"""
    log("构建记忆关联图谱...")
    
    ms = get_memory_system()
    long_term_file = MEMORY_DIR / "vector/long_term_memories.json"
    
    if not long_term_file.exists():
        log("  长期记忆为空")
        return 0
    
    with open(long_term_file, 'r', encoding='utf-8') as f:
        memories = json.load(f)
    
    associations_created = 0
    
    # 简单的关键词关联（后续改为语义相似度）
    for i, m1 in enumerate(memories):
        for m2 in memories[i+1:]:
            # 检查是否有共同标签
            common_tags = set(m1.get("tags", [])) & set(m2.get("tags", []))
            if common_tags:
                for tag in common_tags:
                    ms.add_association(m1["id"], m2["id"], f"共同标签:{tag}")
                    associations_created += 1
    
    log(f"  创建 {associations_created} 条关联")
    return associations_created


def generate_memory_summary():
    """生成记忆摘要报告"""
    log("生成记忆摘要...")
    
    ms = get_memory_system()
    
    # 统计各层记忆数量
    short_term_file = MEMORY_DIR / "temp/short_term.json"
    long_term_file = MEMORY_DIR / "vector/long_term_memories.json"
    assoc_file = MEMORY_DIR / "associations/memory_graph.json"
    
    stats = {
        "short_term": 0,
        "long_term": 0,
        "associations": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    if short_term_file.exists():
        with open(short_term_file, 'r') as f:
            stats["short_term"] = len(json.load(f))
    
    if long_term_file.exists():
        with open(long_term_file, 'r') as f:
            stats["long_term"] = len(json.load(f))
    
    if assoc_file.exists():
        with open(assoc_file, 'r') as f:
            graph = json.load(f)
            stats["associations"] = sum(len(v) for v in graph.values())
    
    # 保存统计
    stats_file = MEMORY_DIR / "archive/memory_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    log(f"  短期记忆: {stats['short_term']} 条")
    log(f"  长期记忆: {stats['long_term']} 条")
    log(f"  记忆关联: {stats['associations']} 条")
    
    return stats


def main():
    """主函数"""
    log("")
    log("🧠 记忆系统自动整理 v5.1")
    log("=" * 60)
    
    results = {
        "daily_extracted": consolidate_daily_files(),
        "archived_to_long": archive_old_short_term(),
        "associations_created": build_memory_associations(),
        "stats": generate_memory_summary()
    }
    
    log("=" * 60)
    log("记忆整理完成")
    log(f"  - 提取每日记忆: {results['daily_extracted']} 条")
    log(f"  - 归档到长期: {results['archived_to_long']} 条")
    log(f"  - 创建关联: {results['associations_created']} 条")
    log("")
    
    return results


if __name__ == "__main__":
    main()
