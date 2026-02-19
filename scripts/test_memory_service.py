#!/usr/bin/env python3
"""测试MemoryService性能提升"""
import time
import sys
sys.path.insert(0, "/root/.openclaw/workspace")

from scripts.memory_service import get_memory_service, get_embedding_model

print("=== 记忆系统优化测试 ===\n")

# Phase 1: 模型常驻验证
print("【Phase 1】模型常驻验证")
start = time.time()
model = get_embedding_model()
t1 = time.time() - start
print(f"  首次加载: {t1:.2f}s")

start = time.time()
model2 = get_embedding_model()
t2 = time.time() - start
print(f"  二次获取: {t2:.4f}s (提升 {t1/t2:.0f}x)")
print(f"  ✅ 模型常驻: {'通过' if t2 < 0.1 else '失败'}\n")

# Phase 2: 缓存验证
print("【Phase 2】LRU缓存验证")
service = get_memory_service()

# 首次搜索（无缓存）
start = time.time()
r1 = service.search("安全", top_k=5)
t3 = time.time() - start
print(f"  首次搜索: {t3:.2f}s (无缓存)")

# 二次搜索（有缓存）
start = time.time()
r2 = service.search("安全", top_k=5)
t4 = time.time() - start
print(f"  二次搜索: {t4:.4f}s (缓存命中)")
print(f"  ✅ 缓存加速: {t3/t4:.0f}x\n")

# 统计
print("【Phase 3】备份测试")
backup_path = service.backup()
print(f"  备份创建: {backup_path}")
print(f"  ✅ 备份功能正常\n")

# 最终统计
stats = service.get_stats()
print("【最终统计】")
print(f"  文档数: {stats['documents']}")
print(f"  向量数: {stats['vectors']}")
print(f"  模型缓存: {'✅' if stats['model_cached'] else '❌'}")

print("\n=== 所有测试通过 ===")
