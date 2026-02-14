#!/usr/bin/env python3
"""
阶段3: 去重清理
基于内容相似度识别和删除重复记录
"""

import json
import pickle
import numpy as np
from collections import defaultdict
from datetime import datetime

WORKSPACE = '/root/.openclaw/workspace/memory/vector'
SIMILARITY_THRESHOLD = 0.95  # 相似度阈值

print("=" * 60)
print("🧹 阶段3: 去重清理")
print("-" * 40)

# 加载阶段2数据
with open(f'{WORKSPACE}/stage2_with_vectors.pkl', 'rb') as f:
    all_memories = pickle.load(f)

print(f"处理前记录数: {len(all_memories)}条")

# 方法1: 基于内容hash的去重
content_to_keys = defaultdict(list)
for key, record in all_memories.items():
    content = record['content'].strip().lower()
    content_to_keys[content].append(key)

# 找出完全重复的内容
exact_duplicates = {content: keys for content, keys in content_to_keys.items() if len(keys) > 1}
print(f"\n📊 完全重复统计:")
print(f"  - 重复内容数: {len(exact_duplicates)}")
print(f"  - 重复总条目: {sum(len(keys) for keys in exact_duplicates.values())}")

# 保留最新的记录，删除其他
keys_to_remove = set()
for content, keys in exact_duplicates.items():
    # 按创建时间排序，保留最新的
    sorted_keys = sorted(keys, key=lambda k: all_memories[k].get('created_at', ''), reverse=True)
    keys_to_remove.update(sorted_keys[1:])  # 保留第一个，删除其他

print(f"  - 将删除: {len(keys_to_remove)}条重复记录")

# 方法2: 基于向量相似度的去重
print(f"\n📊 基于向量相似度的去重...")

# 收集所有向量
keys_list = list(all_memories.keys())
embeddings = []
valid_keys = []

for key in keys_list:
    if key not in keys_to_remove:
        emb = all_memories[key].get('embedding')
        if emb is not None:
            embeddings.append(np.array(emb))
            valid_keys.append(key)

embeddings = np.array(embeddings)
print(f"  - 有效向量数: {len(embeddings)}")

# 计算余弦相似度矩阵
if len(embeddings) > 1:
    # 归一化
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)
    
    # 计算相似度
    similarity_matrix = np.dot(normalized, normalized.T)
    
    # 找出高相似度对（排除对角线）
    similar_pairs = []
    for i in range(len(valid_keys)):
        for j in range(i+1, len(valid_keys)):
            if similarity_matrix[i, j] > SIMILARITY_THRESHOLD:
                similar_pairs.append((valid_keys[i], valid_keys[j], similarity_matrix[i, j]))
    
    print(f"  - 高相似度对: {len(similar_pairs)}对")
    
    # 保留最新的，删除其他的
    semantic_duplicates_removed = 0
    for key1, key2, sim in similar_pairs:
        if key1 not in keys_to_remove and key2 not in keys_to_remove:
            # 比较创建时间，保留新的
            t1 = all_memories[key1].get('created_at', '')
            t2 = all_memories[key2].get('created_at', '')
            if t1 > t2:
                keys_to_remove.add(key2)
            else:
                keys_to_remove.add(key1)
            semantic_duplicates_removed += 1
    
    print(f"  - 语义重复删除: {semantic_duplicates_removed}条")

# 执行删除
cleaned_memories = {k: v for k, v in all_memories.items() if k not in keys_to_remove}

print(f"\n✓ 去重完成:")
print(f"  - 原始记录: {len(all_memories)}条")
print(f"  - 删除记录: {len(keys_to_remove)}条")
print(f"  - 保留记录: {len(cleaned_memories)}条")

# 保存阶段3结果
with open(f'{WORKSPACE}/stage3_deduplicated.pkl', 'wb') as f:
    pickle.dump(cleaned_memories, f)

# 同时保存JSON版本
json_output = {}
for key, record in cleaned_memories.items():
    json_output[key] = {
        **{k: v for k, v in record.items() if k != 'embedding'},
        'embedding': record['embedding'] if isinstance(record['embedding'], list) else 
                      (record['embedding'].tolist() if hasattr(record['embedding'], 'tolist') else None)
    }

with open(f'{WORKSPACE}/stage3_deduplicated.json', 'w') as f:
    json.dump(json_output, f, indent=2)

print(f"\n✓ 阶段3结果已保存")

print("\n" + "=" * 60)
print(f"✓ 去重完成: {len(all_memories)} → {len(cleaned_memories)} 条记录")
print("=" * 60)
