#!/usr/bin/env python3
"""
向量记忆整理脚本
执行去重、过期清理、相似合并
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE = Path.home() / ".openclaw/workspace"
sys.path.insert(0, str(WORKSPACE))

from memory_adapter import get_memory_adapter

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def deduplicate_vectors():
    """删除语义相似的重复向量"""
    log("🔍 开始去重检查...")
    adapter = get_memory_adapter()
    
    if adapter._memory is None:
        log("❌ 向量记忆未初始化")
        return 0
    
    # 获取所有记忆
    all_records = adapter._memory.vector_store.get_all()
    log(f"📊 当前共 {len(all_records)} 条向量")
    
    if len(all_records) < 10:
        log("⚠️ 数据量太小，跳过去重")
        return 0
    
    # 提取向量和ID
    vectors = []
    ids = []
    for r in all_records:
        if "vector" in r:
            vectors.append(r["vector"])
            ids.append(r["id"])
    
    if not vectors:
        log("⚠️ 没有向量数据")
        return 0
    
    vectors = np.array(vectors)
    
    # 计算相似度矩阵
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors_norm = vectors / (norms + 1e-8)
    similarity_matrix = np.dot(vectors_norm, vectors_norm.T)
    
    # 找出相似度>0.95的对（排除对角线）
    threshold = 0.95
    to_delete = set()
    
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if similarity_matrix[i, j] > threshold:
                # 保留较新的
                time_i = all_records[i].get("created_at", "")
                time_j = all_records[j].get("created_at", "")
                if time_i < time_j:
                    to_delete.add(ids[i])
                else:
                    to_delete.add(ids[j])
    
    # 执行删除
    deleted = 0
    for record_id in to_delete:
        if adapter._memory.vector_store.delete(record_id):
            deleted += 1
    
    log(f"✅ 去重完成：删除 {deleted} 条重复向量")
    return deleted

def cleanup_expired_daily():
    """清理过期的daily记录（2年前）"""
    log("🧹 开始过期清理...")
    
    daily_dir = WORKSPACE / "memory/daily"
    if not daily_dir.exists():
        log("⚠️ daily目录不存在")
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=365*2)  # 2年前
    deleted = 0
    
    for file_path in daily_dir.glob("*.md"):
        # 解析文件名日期
        try:
            date_str = file_path.stem[:10]  # 2026-02-10
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if file_date < cutoff_date:
                file_path.unlink()
                deleted += 1
                log(f"  🗑️ 删除过期: {file_path.name}")
        except:
            pass
    
    log(f"✅ 过期清理完成：删除 {deleted} 个文件")
    return deleted

def merge_similar_memories():
    """合并高度相似的记忆"""
    log("🔄 开始相似合并...")
    # 此功能较复杂，先跳过，后续实现
    log("⏭️  相似合并功能待实现")
    return 0

def optimize_index():
    """优化向量索引"""
    log("⚡ 开始索引优化...")
    adapter = get_memory_adapter()
    
    if adapter._memory:
        adapter._memory.optimize()
        log("✅ 索引优化完成")
        return True
    return False

def main():
    log("=" * 50)
    log("🧹 向量记忆整理开始")
    log("=" * 50)
    
    stats = {
        "duplicates_removed": deduplicate_vectors(),
        "expired_cleaned": cleanup_expired_daily(),
        "similar_merged": merge_similar_memories(),
        "optimized": optimize_index()
    }
    
    log("=" * 50)
    log("📊 整理报告")
    log(f"  去重删除: {stats['duplicates_removed']} 条")
    log(f"  过期清理: {stats['expired_cleaned']} 个文件")
    log(f"  相似合并: {stats['similar_merged']} 组")
    log(f"  索引优化: {'✅' if stats['optimized'] else '❌'}")
    log("=" * 50)
    
    return stats

if __name__ == "__main__":
    main()
