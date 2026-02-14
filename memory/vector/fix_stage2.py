#!/usr/bin/env python3
"""
阶段2: 向量重建
使用 sentence-transformers all-MiniLM-L6-v2 (768维) 统一生成向量
"""

import json
import pickle
import numpy as np
from datetime import datetime
import os
import sys

WORKSPACE = '/root/.openclaw/workspace/memory/vector'
TARGET_DIM = 384  # all-MiniLM-L6-v2 输出384维

print("=" * 60)
print("🔧 阶段2: 向量重建")
print("-" * 40)

# 加载阶段1数据
with open(f'{WORKSPACE}/stage1_merged.json', 'r') as f:
    all_memories = json.load(f)

print(f"待处理记录: {len(all_memories)}条")

# 尝试导入sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    print("✓ sentence-transformers已安装")
    
    # 加载模型
    model_name = 'all-MiniLM-L6-v2'
    print(f"正在加载模型: {model_name}...")
    model = SentenceTransformer(model_name)
    print(f"✓ 模型加载完成")
    print(f"  输出维度: {model.get_sentence_embedding_dimension()}")
    
    actual_dim = model.get_sentence_embedding_dimension()
    
except ImportError:
    print("⚠️  sentence-transformers未安装")
    print("正在安装...")
    os.system(f'{sys.executable} -m pip install sentence-transformers -q')
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    actual_dim = model.get_sentence_embedding_dimension()

# 收集需要生成向量的内容
to_embed = []
to_embed_keys = []

for key, record in all_memories.items():
    # 检查是否需要重新生成向量
    needs_embedding = True
    if record.get('embedding') is not None:
        # 检查现有向量维度
        emb = record['embedding']
        if isinstance(emb, list):
            if len(emb) == actual_dim:
                needs_embedding = False
        elif isinstance(emb, np.ndarray):
            if emb.shape[0] == actual_dim:
                needs_embedding = False
    
    if needs_embedding:
        to_embed.append(record['content'])
        to_embed_keys.append(key)

print(f"\n需要生成向量: {len(to_embed)}条")

# 批量生成向量
batch_size = 32
all_embeddings = {}

if len(to_embed) > 0:
    print("正在生成向量...")
    for i in range(0, len(to_embed), batch_size):
        batch = to_embed[i:i+batch_size]
        batch_keys = to_embed_keys[i:i+batch_size]
        
        # 生成向量
        embeddings = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        
        for key, emb in zip(batch_keys, embeddings):
            all_memories[key]['embedding'] = emb.tolist()
            all_memories[key]['has_embedding'] = True
        
        if (i // batch_size) % 10 == 0:
            print(f"  进度: {min(i+batch_size, len(to_embed))}/{len(to_embed)}")
    
    print(f"✓ 向量生成完成")
else:
    print("✓ 所有记录已有正确维度向量")

# 验证所有向量
print("\n验证向量质量...")
invalid_count = 0
for key, record in all_memories.items():
    emb = record.get('embedding')
    if emb is None:
        invalid_count += 1
        print(f"  ⚠️  {key}: 无向量")
    else:
        emb_array = np.array(emb)
        if np.isnan(emb_array).any():
            invalid_count += 1
            print(f"  ⚠️  {key}: 包含NaN")
        if np.isinf(emb_array).any():
            invalid_count += 1
            print(f"  ⚠️  {key}: 包含Inf")

print(f"✓ 验证完成，无效向量: {invalid_count}条")

# 保存阶段2结果
output_data = {}
for key, record in all_memories.items():
    output_data[key] = {
        **record,
        'embedding': record['embedding'] if isinstance(record['embedding'], list) else 
                      (record['embedding'].tolist() if hasattr(record['embedding'], 'tolist') else None)
    }

with open(f'{WORKSPACE}/stage2_with_vectors.json', 'w') as f:
    json.dump(output_data, f, indent=2)

# 同时保存为pickle
with open(f'{WORKSPACE}/stage2_with_vectors.pkl', 'wb') as f:
    pickle.dump(all_memories, f)

print(f"\n✓ 阶段2结果已保存")
print(f"  - JSON: stage2_with_vectors.json")
print(f"  - Pickle: stage2_with_vectors.pkl")

# 统计
print("\n" + "=" * 60)
print(f"✓ 所有 {len(all_memories)} 条记录现在有 {actual_dim} 维向量")
print("=" * 60)
