#!/usr/bin/env python3
"""
完全独立的记忆导入修复脚本
直接使用 LanceDB + HuggingFace，不依赖项目模块
"""
import os
import sys
import time
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import numpy as np
import lancedb
import pyarrow as pa
from tqdm import tqdm

# 需要安装: pip install lancedb sentence-transformers pyarrow tqdm

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("错误: 需要安装 sentence-transformers")
    print("运行: pip install sentence-transformers")
    sys.exit(1)

# 配置
MEMORY_DIR = Path('/root/.openclaw/workspace/memory')
DB_PATH = MEMORY_DIR / 'vector/production'
MODEL_NAME = "BAAI/bge-large-zh-v1.5"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_DIM = 1024

@dataclass
class SimpleVectorStore:
    """简化版向量存储"""
    db_path: Path
    table_name: str = "memories"
    embedding_dim: int = 1024
    
    def __post_init__(self):
        self.db = lancedb.connect(str(self.db_path))
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
    
    def search(self, query_embedding: np.ndarray, top_k: int = 10):
        """语义搜索"""
        results = self.table.search(query_embedding.tolist()).limit(top_k).to_pandas()
        return results
    
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


class SimpleEmbedder:
    """简化版嵌入器"""
    def __init__(self, model_name: str = MODEL_NAME, device: str = "cpu"):
        print(f"正在加载模型: {model_name}...")
        # 检测设备 - 如果不支持CUDA就用CPU
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        except:
            device = "cpu"
        print(f"使用设备: {device}")
        self.model = SentenceTransformer(model_name, device=device)
        self.model_name = model_name
        print("✓ 模型加载完成")
    
    def encode(self, texts: List[str], show_progress: bool = False) -> np.ndarray:
        """编码文本"""
        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=show_progress
        )


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


def import_memories():
    """导入所有记忆文件"""
    print("=" * 60)
    print("🚀 开始修复记忆导入 (独立版本)")
    print("=" * 60)
    
    # 1. 找到所有记忆文件
    md_files = []
    
    for root, dirs, files in os.walk(MEMORY_DIR):
        if 'vector' in root or 'node_modules' in root or '.git' in root:
            continue
        for f in files:
            if f.endswith('.md'):
                md_files.append(Path(root) / f)
    
    print(f"\n📁 找到 {len(md_files)} 个 Markdown 文件")
    
    # 2. 初始化
    print("\n🔧 初始化向量数据库...")
    store = SimpleVectorStore(db_path=DB_PATH, embedding_dim=EMBEDDING_DIM)
    store.initialize()
    
    current_count = store.count()
    print(f"📊 当前数据库: {current_count} 条向量")
    
    if current_count > 0:
        print("⚠️  将清空后重新导入...")
        store.delete_all()
        print("✓ 已清空")
    
    print("\n🔧 加载嵌入模型...")
    embedder = SimpleEmbedder(MODEL_NAME)
    
    # 3. 处理文件
    total_chunks = 0
    processed_files = 0
    errors = []
    
    print(f"\n📖 开始导入 {len(md_files)} 个文件...")
    
    for i, filepath in enumerate(tqdm(md_files, desc="导入进度"), 1):
        try:
            # 读取文件
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                continue
            
            # 分块
            chunks = chunk_text(content, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
            
            if not chunks:
                continue
            
            # 批量编码
            embeddings = embedder.encode(chunks, show_progress=False)
            
            # 准备记录
            records = []
            rel_path = str(filepath.relative_to(MEMORY_DIR))
            for j, (chunk_text_content, embedding) in enumerate(zip(chunks, embeddings)):
                meta = {
                    "source": rel_path,
                    "chunk_index": j,
                    "total_chunks": len(chunks),
                }
                records.append((embedding, chunk_text_content, meta))
            
            # 批量添加
            if records:
                store.add_batch(records)
                total_chunks += len(records)
                processed_files += 1
                
        except Exception as e:
            errors.append((filepath, str(e)))
    
    # 4. 优化
    print("\n🔍 优化索引...")
    store.optimize()
    
    # 5. 统计
    final_count = store.count()
    print("\n" + "=" * 60)
    print("✅ 导入完成!")
    print("=" * 60)
    print(f"\n📊 统计:")
    print(f"   - 处理文件: {processed_files}/{len(md_files)}")
    print(f"   - 总块数: {total_chunks}")
    print(f"   - 最终向量: {final_count}")
    print(f"   - 错误数: {len(errors)}")
    
    if errors:
        print(f"\n⚠️  错误详情 (前5个):")
        for filepath, err in errors[:5]:
            print(f"   - {filepath.name}: {err}")
    
    return store, embedder, final_count


def test_performance(store, embedder):
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
        query_emb = embedder.encode([query])[0]
        results = store.search(query_emb, top_k=3)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        print(f'   "{query}": {elapsed:.1f}ms - {len(results)}条结果')
    
    avg_time = sum(times) / len(times)
    print(f"\n📈 平均查询时间: {avg_time:.1f}ms")
    
    # 展示详细结果
    print("\n📝 示例查询 (\"自主进化\"):")
    query_emb = embedder.encode(["自主进化"])[0]
    results = store.search(query_emb, top_k=2)
    for i, row in results.iterrows():
        preview = row['content'][:120].replace('\n', ' ')
        print(f"   {i+1}. [{row.get('_distance', 0):.3f}] {preview}...")
        print(f"      来源: {row.get('source', 'unknown')}")
    
    return avg_time


if __name__ == "__main__":
    # 执行导入
    store, embedder, final_count = import_memories()
    
    # 测试性能
    if final_count > 0:
        avg_time = test_performance(store, embedder)
        
        # 完成
        print("\n" + "=" * 60)
        print("🎉 修复完成!")
        print("=" * 60)
        print(f"\n✅ 向量记忆系统已就绪")
        print(f"   - 数据库: {final_count} 条向量")
        print(f"   - 平均查询: {avg_time:.1f}ms")
        
        if final_count < 50:
            print(f"\n⚠️  警告: 向量数较少，可能部分文件未成功导入")
    else:
        print("\n❌ 导入失败，数据库为空")
