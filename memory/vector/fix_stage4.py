#!/usr/bin/env python3
"""
阶段4: LanceDB重建
清理现有LanceDB表，导入统一后的数据，建立新索引
"""

import json
import pickle
import numpy as np
import os
import shutil
from datetime import datetime

WORKSPACE = '/root/.openclaw/workspace/memory/vector'
LANCE_PATH = f'{WORKSPACE}/production/memories.lance'

print("=" * 60)
print("🗄️ 阶段4: LanceDB重建")
print("-" * 40)

# 加载阶段3数据
with open(f'{WORKSPACE}/stage3_deduplicated.pkl', 'rb') as f:
    cleaned_memories = pickle.load(f)

print(f"待导入记录: {len(cleaned_memories)}条")

# 清理现有LanceDB
print("\n清理现有LanceDB...")
if os.path.exists(LANCE_PATH):
    try:
        # 尝试删除整个目录
        shutil.rmtree(LANCE_PATH)
        print(f"✓ 已删除旧LanceDB: {LANCE_PATH}")
    except Exception as e:
        print(f"⚠️  删除失败: {e}")
        # 尝试重命名备份
        backup_path = f"{LANCE_PATH}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            os.rename(LANCE_PATH, backup_path)
            print(f"✓ 已备份到: {backup_path}")
        except:
            pass

# 准备数据
print("\n准备数据...")
import pandas as pd

records = []
for key, record in cleaned_memories.items():
    emb = record.get('embedding')
    if emb is None:
        print(f"⚠️  跳过无向量记录: {key}")
        continue
    
    if isinstance(emb, list):
        vector = emb
    elif hasattr(emb, 'tolist'):
        vector = emb.tolist()
    else:
        vector = list(emb)
    
    records.append({
        'id': record.get('id', key),
        'content': record['content'],
        'source': record.get('source', 'unknown'),
        'type': record.get('type', 'general'),
        'importance': record.get('importance', 5),
        'tags': json.dumps(record.get('tags', [])),
        'created_at': record.get('created_at', datetime.now().isoformat()),
        'access_count': record.get('access_count', 0),
        'vector': vector
    })

print(f"✓ 有效记录: {len(records)}条")

if len(records) == 0:
    print("❌ 无有效记录，中止")
    exit(1)

# 创建DataFrame
df = pd.DataFrame(records)
print(f"✓ DataFrame创建完成: {len(df)}行 x {len(df.columns)}列")
print(f"  向量维度: {len(df['vector'].iloc[0])}")

# 连接到LanceDB并创建表
print("\n创建LanceDB表...")
import lancedb

# 确保目录存在
os.makedirs(os.path.dirname(LANCE_PATH), exist_ok=True)

# 连接数据库
db = lancedb.connect(LANCE_PATH)

# 创建表
table = db.create_table(
    "memories",
    data=df,
    mode="overwrite"
)

print(f"✓ 表创建完成: {table.name}")
print(f"  行数: {table.count_rows()}")

# 创建索引
print("\n创建向量索引...")
try:
    table.create_index(
        metric="cosine",
        vector_column_name="vector",
        num_partitions=2 if len(records) < 100 else 8
    )
    print("✓ 向量索引创建完成")
except Exception as e:
    print(f"⚠️  索引创建失败: {e}")
    print("  数据仍可搜索，但性能可能较低")

# 验证检索功能
print("\n验证检索功能...")
try:
    # 使用第一条记录的向量进行搜索
    test_vector = df['vector'].iloc[0]
    results = table.search(test_vector).limit(3).to_pandas()
    print(f"✓ 检索测试成功，返回{len(results)}条结果")
except Exception as e:
    print(f"⚠️  检索测试失败: {e}")

print("\n" + "=" * 60)
print(f"✓ LanceDB重建完成")
print(f"  - 记录数: {table.count_rows()}")
print(f"  - 位置: {LANCE_PATH}")
print("=" * 60)
