#!/usr/bin/env python3
"""
优化版记忆导入 - 批量处理所有文本块
"""
import os
import sys
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import lancedb
import pyarrow as pa
from tqdm import tqdm

from sentence_transformers import SentenceTransformer

# 配置
MEMORY_DIR = Path('/root/.openclaw/workspace/memory')
DB_PATH = MEMORY_DIR / 'vector/production'
MODEL_NAME = "BAAI/bge-large-zh-v1.5"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_DIM = 1024
BATCH_SIZE = 32  # 减小批次大小避免内存问题

class SimpleVectorStore:
    """简化版向量存储"""
    def __init__(self, db_path: Path, table_name: str = "memories", embedding_dim: int = 1024):
        self.db_path = db_path
        self.table_name = table_name
        self.embedding_dim = embedding_dim
        self.db = lancedb.connect(str(db_path))
        self.table = None
        
    def initialize(self):
        """初始化表"""
        schema = pa.schema([
            ("id", pa.string()),
            ("vector", pa.list_(pa.float32(), self.embedding_dim)),
            ("content", pa.string()),
            ("source", pa.string()),
            ("metadata", pa.string()),
            ("created_at", pa.string()),
        ])
        
        try:
            self.table = self.db.open_table(self.table_name)
        except:
            self.table = self.db.create_table(self.table_name, schema=schema)
    
    def add_batch(self, records: List[tuple]):
        """批量添加记录 (embedding, content, metadata)"""
        data = []
        for i, (embedding, content, meta) in enumerate(records):
            record_id = hashlib.sha256(f"{meta.get('source', '')}:{i}:{time.time()}".encode()).hexdigest()[:16]
            data.append({
                "id": record_id,
                "vector": embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding),
                "content": content,
                "source": meta.get("source", "unknown"),
                "metadata": json.dumps(meta, ensure_ascii=False),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
        
        if data:
            self.table.add(data)
    
    def count(self):
        return self.table.count_rows()
    
    def delete_all(self):
        """清空表"""
        try:
            self.db.drop_table(self.table_name)
            self.initialize()
        except:
            pass
    
    def optimize(self):
        """优化索引"""
        try:
            self.table.optimize()
        except:
            pass


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """将文本分块"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def collect_all_chunks() -> List[Tuple[str, Dict]]:
    """
    收集所有文件的文本块，返回 (chunk_text, metadata) 列表
    """
    print("📁 扫描记忆文件...")
    
    md_files = []
    for root, dirs, files in os.walk(MEMORY_DIR):
        if 'vector' in root or 'node_modules' in root or '.git' in root:
            continue
        for f in files:
            if f.endswith('.md'):
                md_files.append(Path(root) / f)
    
    print(f"   找到 {len(md_files)} 个 Markdown 文件")
    
    all_chunks = []
    errors = []
    
    for filepath in tqdm(md_files, desc="   读取文件"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                continue
            
            # 分块
            chunks = chunk_text(content, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
            
            # 为每个块创建元数据
            rel_path = str(filepath.relative_to(MEMORY_DIR))
            for j, chunk_text_content in enumerate(chunks):
                meta = {
                    "source": rel_path,
                    "chunk_index": j,
                    "total_chunks": len(chunks),
                }
                all_chunks.append((chunk_text_content, meta))
                
        except Exception as e:
            errors.append((filepath, str(e)))
    
    print(f"\n   ✓ 共收集 {len(all_chunks)} 个文本块")
    if errors:
        print(f"   ⚠️  {len(errors)} 个文件读取失败")
    
    return all_chunks


def batch_encode(chunks: List[Tuple[str, Dict]], model: SentenceTransformer, batch_size: int = 64) -> List[Tuple[np.ndarray, str, Dict]]:
    """
    批量编码所有文本块
    返回 (embedding, content, metadata) 列表
    """
    print("\n🔧 批量编码文本块...")
    
    results = []
    texts = [c[0] for c in chunks]
    metadatas = [c[1] for c in chunks]
    
    # 批量编码
    for i in tqdm(range(0, len(texts), batch_size), desc="   编码进度"):
        batch_texts = texts[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        
        embeddings = model.encode(
            batch_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        for emb, text, meta in zip(embeddings, batch_texts, batch_metas):
            results.append((emb, text, meta))
    
    return results


def import_memories():
    """导入所有记忆文件"""
    print("=" * 60)
    print("🚀 开始优化版记忆导入")
    print("=" * 60)
    
    # 1. 收集所有文本块
    all_chunks = collect_all_chunks()
    
    if not all_chunks:
        print("\n❌ 没有找到可导入的内容")
        return
    
    # 2. 初始化数据库
    print("\n🔧 初始化向量数据库...")
    store = SimpleVectorStore(db_path=DB_PATH, embedding_dim=EMBEDDING_DIM)
    store.initialize()
    
    current_count = store.count()
    print(f"   当前数据库: {current_count} 条向量")
    if current_count > 0:
        print("   ⚠️  将清空后重新导入...")
        store.delete_all()
    
    # 3. 加载模型
    print("\n🔧 加载嵌入模型...")
    print(f"   模型: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    print("   ✓ 模型加载完成")
    
    # 4. 批量编码
    encoded_records = batch_encode(all_chunks, model, batch_size=BATCH_SIZE)
    
    # 5. 批量存储
    print("\n💾 存储到向量数据库...")
    store.add_batch(encoded_records)
    
    # 6. 优化索引
    print("\n🔍 优化索引...")
    store.optimize()
    
    # 7. 统计
    final_count = store.count()
    print("\n" + "=" * 60)
    print("✅ 导入完成!")
    print("=" * 60)
    print(f"\n📊 统计:")
    print(f"   - 处理文件: {len(set(m['source'] for _, m in all_chunks))}")
    print(f"   - 总块数: {len(all_chunks)}")
    print(f"   - 最终向量: {final_count}")
    
    return store, model, final_count


def test_performance(store, model):
    """测试查询性能"""
    print("\n" + "=" * 60)
    print("🧪 测试查询性能")
    print("=" * 60)
    
    test_queries = [
        ("用户偏好", "用户习惯和偏好设置"),
        ("自主进化", "系统自我改进机制"),
        ("Moltbook", "社区和交流平台"),
        ("备份策略", "数据备份和恢复"),
        ("飞书配置", "飞书渠道设置"),
        ("向量记忆", "语义搜索系统"),
        ("高可用架构", "容错和集群设计"),
        ("永生计划", "长期生存保障"),
    ]
    
    times = []
    for query, desc in test_queries:
        start = time.time()
        query_emb = model.encode([query], normalize_embeddings=True)[0]
        results = store.table.search(query_emb.tolist()).limit(3).to_pandas()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        print(f'   "{query}": {elapsed:.1f}ms - {len(results)}条结果')
    
    avg_time = sum(times) / len(times)
    print(f"\n📈 平均查询时间: {avg_time:.1f}ms")
    
    # 展示示例结果
    print("\n📝 示例查询 (\"自主进化\"):")
    query_emb = model.encode(["自主进化"], normalize_embeddings=True)[0]
    results = store.table.search(query_emb.tolist()).limit(2).to_pandas()
    for i, row in results.iterrows():
        preview = row['content'][:120].replace('\n', ' ')
        print(f"   {i+1}. [{row.get('_distance', 0):.3f}] {preview}...")
        print(f"      来源: {row.get('source', 'unknown')}")
    
    return avg_time


if __name__ == "__main__":
    # 执行导入
    store, model, final_count = import_memories()
    
    # 测试性能
    if final_count > 0:
        avg_time = test_performance(store, model)
        
        # 完成
        print("\n" + "=" * 60)
        print("🎉 修复完成!")
        print("=" * 60)
        print(f"\n✅ 向量记忆系统已就绪")
        print(f"   - 数据库: {final_count} 条向量")
        print(f"   - 平均查询: {avg_time:.1f}ms")
    else:
        print("\n❌ 导入失败，数据库为空")
