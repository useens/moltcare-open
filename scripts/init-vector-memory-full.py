#!/usr/bin/env python3
"""
向量记忆系统初始化与测试
夜间进化第2轮 - 核心修复脚本
"""

import sys
import os
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace'))

import numpy as np
from sentence_transformers import SentenceTransformer
from core.vector_memory.vector_store import VectorStore
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 初始化嵌入模型
logger.info("加载嵌入模型...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
logger.info(f"✅ 模型加载成功，维度: {model.get_sentence_embedding_dimension()}")

# 初始化向量存储
store = VectorStore('data/vector_memory')
logger.info("✅ 向量存储初始化成功")

# 测试数据
test_memories = [
    ("夜间进化第2轮启动，系统优化进行中", {"source": "night-evolution", "round": 2, "type": "system"}),
    ("向量记忆系统初始化完成，LanceDB后端", {"source": "vector-memory", "status": "initialized"}),
    ("深度学习债务处理，Signal 10优先级", {"source": "learning-debt", "priority": "high"}),
    ("Moltbook社区内容策略准备", {"source": "moltbook", "type": "strategy"}),
    ("系统自动化增强，创建新脚本", {"source": "automation", "type": "enhancement"}),
]

# 批量添加
def add_with_embedding(content, metadata):
    """生成嵌入并添加记录"""
    embedding = model.encode(content, convert_to_numpy=True)
    return store.add(embedding, content, metadata)

logger.info("添加测试记忆...")
record_ids = []
for content, metadata in test_memories:
    rid = add_with_embedding(content, metadata)
    record_ids.append(rid)
    logger.info(f"  ✅ {rid[:8]}... {content[:30]}...")

logger.info(f"✅ 成功添加 {len(record_ids)} 条测试记忆")

# 测试检索
logger.info("\n测试语义检索...")
queries = ["系统优化", "向量记忆", "深度学习"]

for query in queries:
    query_embedding = model.encode(query, convert_to_numpy=True)
    results = store.search(query_embedding, limit=3)
    logger.info(f"\n  查询: '{query}'")
    for r in results:
        content = r.get('content', '')[:40]
        score = r.get('_distance', 0)
        logger.info(f"    → {content}... (score: {score:.3f})")

# 获取统计
stats = store.get_stats()
logger.info(f"\n📊 向量存储统计:")
logger.info(f"  - 总记录数: {stats.get('total_records', 0)}")
logger.info(f"  - 向量维度: {stats.get('vector_dim', 0)}")
logger.info(f"  - 存储路径: data/vector_memory")

logger.info("\n✅ 向量记忆系统初始化与测试完成")
