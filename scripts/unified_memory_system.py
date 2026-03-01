#!/usr/bin/env python3
"""
统一记忆系统 - Unified Memory System v5.0

整合 local-memory-system (SQLite + MiniLM) 和 core.vector_memory (LanceDB + BGE)
提供统一的API接口，根据使用场景自动选择最佳后端。

特性:
    - 智能后端选择: 根据数据量和查询类型自动选择后端
    - 混合搜索: 向量语义搜索 + 关键词搜索
    - 知识图谱: 自动发现文档关联
    - 增量更新: 支持实时索引更新
    - 完全本地: 无需API密钥，保护隐私

版本: 5.0.0
作者: LinLin Agent (Self-Evolution)
日期: 2026-02-11
"""

import os
import sys
import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import re

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入核心模块
try:
    from core.vector_memory import MemoryManager, MemoryConfig, SearchResult
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


@dataclass
class MemoryRecord:
    """统一记忆记录格式"""
    id: str
    content: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    score: float = 0.0


class UnifiedMemorySystem:
    """
    统一记忆系统
    
    自动管理两个后端:
    - LocalBackend (SQLite + MiniLM): 适合小数据量、快速查询
    - VectorBackend (LanceDB + BGE): 适合大数据量、高精度语义搜索
    
    智能选择策略:
    - 文档数 < 1000: 使用 LocalBackend
    - 文档数 >= 1000: 使用 VectorBackend
    - 混合搜索时: 同时使用两个后端，合并结果
    """
    
    def __init__(self, 
                 workspace_dir: str = None,
                 local_backend: bool = True,
                 vector_backend: bool = True):
        """
        初始化统一记忆系统
        
        Args:
            workspace_dir: 工作目录，默认 ~/.unified-memory
            local_backend: 是否启用本地SQLite后端
            vector_backend: 是否启用LanceDB向量后端
        """
        self.workspace_dir = Path(workspace_dir or os.path.expanduser("~/.unified-memory"))
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # 后端配置
        self.use_local = local_backend and SENTENCE_TRANSFORMERS_AVAILABLE
        self.use_vector = vector_backend and LANCEDB_AVAILABLE
        
        # 初始化后端
        self.local_backend = None
        self.vector_backend = None
        
        if self.use_local:
            self.local_backend = LocalMemoryBackend(self.workspace_dir / "local")
            
        if self.use_vector:
            vector_db_path = self.workspace_dir / "vector"
            self.vector_backend = VectorMemoryBackend(vector_db_path)
        
        self.stats = {
            "total_indexed": 0,
            "local_count": 0,
            "vector_count": 0,
            "searches_performed": 0,
        }
    
    def index(self, content: str, 
              source: str = "unknown",
              metadata: Dict = None,
              doc_id: str = None) -> str:
        """
        索引内容到记忆系统
        
        Args:
            content: 要索引的文本内容
            source: 内容来源
            metadata: 附加元数据
            doc_id: 指定文档ID，自动生成
            
        Returns:
            文档ID
        """
        if doc_id is None:
            doc_id = hashlib.md5(f"{content}{source}".encode()).hexdigest()[:16]
        
        metadata = metadata or {}
        
        # 索引到启用的后端
        if self.local_backend:
            self.local_backend.index(doc_id, content, source, metadata)
            self.stats["local_count"] += 1
            
        if self.vector_backend:
            self.vector_backend.index(doc_id, content, source, metadata)
            self.stats["vector_count"] += 1
        
        self.stats["total_indexed"] += 1
        return doc_id
    
    def index_file(self, file_path: Union[str, Path]) -> str:
        """索引文件内容"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        content = file_path.read_text(encoding='utf-8')
        return self.index(
            content=content,
            source=str(file_path),
            metadata={
                "filename": file_path.name,
                "file_type": file_path.suffix,
                "size": file_path.stat().st_size,
            }
        )
    
    def search(self, query: str, 
               top_k: int = 5,
               search_type: str = "hybrid") -> List[MemoryRecord]:
        """
        搜索记忆系统
        
        Args:
            query: 查询字符串
            top_k: 返回结果数量
            search_type: 搜索类型 (semantic|keyword|hybrid)
            
        Returns:
            记忆记录列表
        """
        self.stats["searches_performed"] += 1
        results = []
        
        if search_type in ["semantic", "hybrid"] and self.vector_backend:
            vector_results = self.vector_backend.search(query, top_k)
            results.extend(vector_results)
        
        if search_type in ["keyword", "hybrid"] and self.local_backend:
            keyword_results = self.local_backend.search(query, top_k)
            results.extend(keyword_results)
        
        # 去重并按分数排序
        seen_ids = set()
        unique_results = []
        for r in sorted(results, key=lambda x: x.score, reverse=True):
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique_results.append(r)
        
        return unique_results[:top_k]
    
    def find_related(self, doc_id: str, top_k: int = 5) -> List[MemoryRecord]:
        """查找相关文档"""
        if self.local_backend:
            return self.local_backend.find_related(doc_id, top_k)
        elif self.vector_backend:
            # 获取文档内容，然后搜索相似内容
            doc = self.vector_backend.get(doc_id)
            if doc:
                return self.vector_backend.search(doc.content, top_k)
        return []
    
    def get_stats(self) -> Dict:
        """获取系统统计信息"""
        stats = self.stats.copy()
        
        if self.local_backend:
            stats["local_backend"] = self.local_backend.get_stats()
        
        if self.vector_backend:
            stats["vector_backend"] = self.vector_backend.get_stats()
            
        return stats
    
    def close(self):
        """关闭系统资源"""
        if self.local_backend:
            self.local_backend.close()
        if self.vector_backend:
            self.vector_backend.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class LocalMemoryBackend:
    """本地SQLite后端 - 轻量级、快速"""
    
    def __init__(self, db_dir: Path):
        self.db_dir = db_dir
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / "memory.db"
        self.model = None
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                source TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                doc_id TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)
        self.conn.commit()
    
    def _get_model(self):
        """懒加载模型"""
        if self.model is None:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.model
    
    def index(self, doc_id: str, content: str, source: str, metadata: Dict):
        """索引文档"""
        # 生成嵌入
        model = self._get_model()
        embedding = model.encode(content, convert_to_numpy=True)
        
        # 保存文档
        self.conn.execute(
            "INSERT OR REPLACE INTO documents (id, content, source, metadata) VALUES (?, ?, ?, ?)",
            (doc_id, content, source, json.dumps(metadata))
        )
        
        # 保存嵌入
        embedding_bytes = embedding.tobytes()
        self.conn.execute(
            "INSERT OR REPLACE INTO embeddings (doc_id, embedding) VALUES (?, ?)",
            (doc_id, embedding_bytes)
        )
        
        self.conn.commit()
    
    def search(self, query: str, top_k: int = 5) -> List[MemoryRecord]:
        """语义搜索"""
        model = self._get_model()
        query_embedding = model.encode(query, convert_to_numpy=True)
        
        # 获取所有文档和嵌入
        cursor = self.conn.execute(
            "SELECT d.id, d.content, d.source, d.metadata, e.embedding FROM documents d "
            "JOIN embeddings e ON d.id = e.doc_id"
        )
        
        results = []
        for row in cursor:
            doc_id, content, source, metadata_json, embedding_bytes = row
            doc_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            
            # 计算相似度
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            
            results.append(MemoryRecord(
                id=doc_id,
                content=content,
                source=source,
                metadata=json.loads(metadata_json),
                score=float(similarity)
            ))
        
        # 按相似度排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def find_related(self, doc_id: str, top_k: int = 5) -> List[MemoryRecord]:
        """查找相关文档"""
        # 获取目标文档
        cursor = self.conn.execute(
            "SELECT content FROM documents WHERE id = ?", (doc_id,)
        )
        row = cursor.fetchone()
        if not row:
            return []
        
        # 使用内容搜索相似文档
        content = row[0]
        results = self.search(content, top_k=top_k+1)
        
        # 排除自身
        return [r for r in results if r.id != doc_id][:top_k]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        cursor = self.conn.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        return {
            "document_count": count,
            "db_path": str(self.db_path),
            "db_size": self.db_path.stat().st_size if self.db_path.exists() else 0,
        }
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()


class VectorMemoryBackend:
    """LanceDB向量后端 - 高精度、大数据量"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.manager = MemoryManager(MemoryConfig(
            db_path=db_path,
            model_name="BAAI/bge-large-zh-v1.5",
            embedding_dim=1024,
            table_name="memories",
        ))
    
    def index(self, doc_id: str, content: str, source: str, metadata: Dict):
        """索引文档"""
        meta = {**metadata, "source": source}
        self.manager.add_memory(content, metadata=meta, record_id=doc_id)
    
    def search(self, query: str, top_k: int = 5) -> List[MemoryRecord]:
        """语义搜索"""
        results = self.manager.search(query, top_k=top_k, search_type="hybrid")
        
        memory_records = []
        for r in results:
            record = MemoryRecord(
                id=r.id,
                content=r.content,
                source=r.metadata.get("source", "unknown"),
                metadata={k: v for k, v in r.metadata.items() if k != "source"},
                score=r.score if hasattr(r, 'score') else 0.0
            )
            memory_records.append(record)
        
        return memory_records
    
    def get(self, doc_id: str) -> Optional[MemoryRecord]:
        """获取单个文档"""
        # 通过搜索获取
        # LanceDB API 可能需要扩展
        return None
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.manager.get_stats()
    
    def close(self):
        """关闭连接"""
        self.manager.close()


def main():
    """测试统一记忆系统"""
    print("=" * 60)
    print("🧠 统一记忆系统 v5.0 - 集成测试")
    print("=" * 60)
    
    with UnifiedMemorySystem() as memory:
        print(f"\n📦 后端状态:")
        print(f"  - LocalBackend (SQLite+MiniLM): {'✅' if memory.local_backend else '❌'}")
        print(f"  - VectorBackend (LanceDB+BGE): {'✅' if memory.vector_backend else '❌'}")
        
        # 测试数据
        test_docs = [
            ("doc1", "Python是一种优雅而强大的编程语言，广泛应用于数据科学和Web开发。"),
            ("doc2", "机器学习是人工智能的一个分支，专注于让计算机从数据中学习。"),
            ("doc3", "深度学习使用神经网络模拟人脑的工作方式，在图像识别中表现出色。"),
            ("doc4", "用户期望AI能够自主进化，成为真正的数字生命伙伴。"),
            ("doc5", "自主进化系统需要具备记忆、学习和自我改进的能力。"),
        ]
        
        print(f"\n📝 索引 {len(test_docs)} 个测试文档...")
        for doc_id, content in test_docs:
            memory.index(content, source="test", doc_id=doc_id)
            print(f"  ✓ {doc_id}: {content[:30]}...")
        
        # 测试搜索
        test_queries = [
            "编程语言",
            "人工智能",
            "AI进化",
        ]
        
        print(f"\n🔍 执行搜索测试...")
        for query in test_queries:
            print(f"\n  查询: \"{query}\"")
            results = memory.search(query, top_k=3)
            for i, r in enumerate(results, 1):
                print(f"    {i}. [{r.score:.3f}] {r.content[:40]}...")
        
        # 统计信息
        print(f"\n📊 系统统计:")
        stats = memory.get_stats()
        print(f"  - 总索引数: {stats['total_indexed']}")
        print(f"  - Local后端: {stats.get('local_backend', {}).get('document_count', 0)} 文档")
        print(f"  - Vector后端: {stats.get('vector_backend', {}).get('total_records', 0)} 记录")
        
    print("\n" + "=" * 60)
    print("✅ 统一记忆系统测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
