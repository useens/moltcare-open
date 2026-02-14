#!/usr/bin/env python3
"""
向量记忆系统紧急修复脚本 (P0级别)
修复目标: 
1. 合并所有存储系统的数据
2. 去除重复内容
3. 统一生成768维向量
4. 重建LanceDB
"""

import json
import pickle
import hashlib
import numpy as np
from datetime import datetime
from collections import defaultdict
import os
import sys

# 配置
WORKSPACE = '/root/.openclaw/workspace/memory/vector'
INPUT_JSON = f'{WORKSPACE}/long_term_memories.json'
INPUT_PKL = f'{WORKSPACE}/memory_vectors.pkl'
LANCE_DB_PATH = f'{WORKSPACE}/production/memories.lance'
OUTPUT_JSON = f'{WORKSPACE}/long_term_memories_fixed.json'
OUTPUT_PKL = f'{WORKSPACE}/memory_vectors_fixed.pkl'

print("=" * 60)
print("🚨 向量记忆系统紧急修复")
print("=" * 60)

# 阶段1: 数据整合
print("\n📦 阶段1: 数据整合")
print("-" * 40)

# 读取JSON数据
with open(INPUT_JSON, 'r') as f:
    json_memories = json.load(f)
print(f"✓ JSON记忆: {len(json_memories)}条")

# 读取Pickle数据
with open(INPUT_PKL, 'rb') as f:
    pkl_data = pickle.load(f)
print(f"✓ Pickle记忆: {len(pkl_data)}条")

# 建立统一数据集
all_memories = {}

# 从JSON导入
for m in json_memories:
    content_hash = hashlib.md5(m['content'].encode()).hexdigest()[:16]
    all_memories[content_hash] = {
        'id': m.get('id', content_hash),
        'content': m['content'],
        'source': m.get('source', 'unknown'),
        'type': m.get('type', 'general'),
        'importance': m.get('importance', 5),
        'tags': m.get('tags', []),
        'created_at': m.get('created_at', datetime.now().isoformat()),
        'access_count': m.get('access_count', 0),
        'last_accessed': m.get('last_accessed', m.get('created_at', datetime.now().isoformat())),
        'has_embedding': False,
        'embedding': None
    }

# 从Pickle导入（优先，因为可能有向量）
embedding_dims = set()
for key, record in pkl_data.items():
    content_hash = hashlib.md5(record['content'].encode()).hexdigest()[:16]
    
    if content_hash in all_memories:
        # 更新现有记录
        all_memories[content_hash]['has_embedding'] = True
        if 'embedding' in record and record['embedding'] is not None:
            emb = record['embedding']
            if isinstance(emb, np.ndarray):
                all_memories[content_hash]['embedding'] = emb
                embedding_dims.add(emb.shape[0] if len(emb.shape) > 0 else len(emb))
            else:
                all_memories[content_hash]['embedding'] = np.array(emb)
                embedding_dims.add(len(emb))
    else:
        # 新增记录
        all_memories[content_hash] = {
            'id': record.get('id', content_hash),
            'content': record['content'],
            'source': record.get('source', 'unknown'),
            'type': record.get('type', 'general'),
            'importance': record.get('importance', 5),
            'tags': record.get('tags', []),
            'created_at': record.get('created_at', datetime.now().isoformat()),
            'access_count': 0,
            'last_accessed': record.get('created_at', datetime.now().isoformat()),
            'has_embedding': True,
            'embedding': None
        }
        if 'embedding' in record and record['embedding'] is not None:
            emb = record['embedding']
            if isinstance(emb, np.ndarray):
                all_memories[content_hash]['embedding'] = emb
                embedding_dims.add(emb.shape[0] if len(emb.shape) > 0 else len(emb))
            else:
                all_memories[content_hash]['embedding'] = np.array(emb)
                embedding_dims.add(len(emb))

print(f"✓ 整合后总记录: {len(all_memories)}条")
print(f"✓ 发现向量维度: {embedding_dims}")

# 统计无向量记录
no_embedding = [k for k, v in all_memories.items() if v['embedding'] is None]
print(f"⚠️  无向量记录: {len(no_embedding)}条")

# 保存中间结果
with open(f'{WORKSPACE}/stage1_merged.json', 'w') as f:
    json.dump({k: {**v, 'embedding': None} for k, v in all_memories.items()}, f, indent=2)
print(f"✓ 阶段1结果已保存")

print("\n" + "=" * 60)
print("阶段1完成 - 发现以下问题需要修复:")
print(f"  • 有{len(no_embedding)}条记录需要重新生成向量")
print(f"  • 向量维度不统一: {embedding_dims}")
print("=" * 60)
