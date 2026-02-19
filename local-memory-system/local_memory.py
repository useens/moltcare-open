#!/usr/bin/env python3
"""
Local Memory System - 本地向量记忆系统

基于 SQLite + MiniLM 的轻量级向量记忆系统，完全离线运行，无需API密钥。
支持语义搜索、关键词搜索和文档关联发现。

主要功能:
    - 文档索引: 将文本文件索引到向量数据库
    - 语义搜索: 基于向量相似度的智能检索
    - 关键词搜索: 传统的文本匹配搜索
    - 关联发现: 自动发现相关文档

技术栈:
    - SQLite: 数据存储
    - MiniLM (all-MiniLM-L6-v2): 文本嵌入模型
    - NumPy: 向量计算

示例:
    >>> from local_memory import LocalMemorySystem
    >>> memory = LocalMemorySystem()
    >>> memory.init()
    >>> memory.index_file("my_notes.md")
    >>> results = memory.search("Python programming", top_k=5)
    >>> for r in results:
    ...     print(f"{r['file_path']}: {r['similarity']:.4f}")

作者: LinLin Agent
版本: 1.0.0
日期: 2026-02-10
"""

import os
import sys
import json
import sqlite3
import argparse
import hashlib
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union

# 嵌入模型导入 - 使用共享模型池
try:
    # 确保能导入共享模型池
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.shared_models import get_model
except ImportError:
    # 如果无法导入共享模型池，回退到原始导入
    try:
        from sentence_transformers import SentenceTransformer
        get_model = None
    except ImportError:
        print("❌ 请先安装依赖: pip install sentence-transformers")
        sys.exit(1)


class LocalMemorySystem:
    """
    本地记忆系统主类
    
    提供完整的文档索引、向量搜索和关联发现功能。
    数据存储在SQLite数据库中，嵌入向量使用MiniLM模型生成。
    
    Attributes:
        memory_dir (Path): 记忆存储目录
        db_path (Path): SQLite数据库文件路径
        model (SentenceTransformer): MiniLM嵌入模型实例
        conn (sqlite3.Connection): 数据库连接
        
    Example:
        >>> memory = LocalMemorySystem("~/.my-memory")
        >>> memory.init()
        >>> memory.index_file("document.md")
        >>> results = memory.search("query", top_k=5)
    """
    
    def __init__(self, memory_dir: str = None):
        """
        初始化记忆系统
        
        Args:
            memory_dir: 记忆存储目录，默认为 ~/.local-memory
            
        Example:
            >>> memory = LocalMemorySystem()  # 使用默认目录
            >>> memory = LocalMemorySystem("/custom/path")  # 自定义目录
        """
        self.memory_dir = Path(memory_dir or os.path.expanduser("~/.local-memory"))
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.memory_dir / "memory.db"
        self.model: Optional[SentenceTransformer] = None
        self.conn: Optional[sqlite3.Connection] = None
        
    def _get_model(self):
        """
        懒加载嵌入模型（使用共享模型池）

        首次调用时会加载 all-MiniLM-L6-v2 模型（约80MB）。
        后续调用返回共享的缓存模型实例，避免重复加载。

        Returns:
            SentenceTransformer: 加载好的MiniLM模型

        Note:
            - 使用共享模型池，模块间共享模型实例
            - 模型文件会缓存到 ~/.cache/torch/sentence_transformers/
            - 二次调用加载时间<100ms
        """
        if self.model is None:
            print("🔄 正在加载 MiniLM 嵌入模型...")
            if get_model is not None:
                # 使用共享模型池
                self.model = get_model("all-MiniLM-L6-v2")
            else:
                # 回退到原始加载方式
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ 模型加载完成")
        return self.model
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        获取数据库连接
        
        使用懒加载模式，首次调用时创建连接。
        
        Returns:
            sqlite3.Connection: SQLite数据库连接
        """
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def init(self) -> None:
        """
        初始化记忆系统
        
        创建数据库表结构，包括：
        - documents: 文档元数据表
        - document_vectors: 向量存储表
        - connections: 文档关联表
        
        如果表已存在，则不会重复创建。
        
        Example:
            >>> memory = LocalMemorySystem()
            >>> memory.init()  # 创建数据库表
        """
        print("🧠 正在初始化本地记忆系统...\n")
        
        # 创建数据库表
        conn = self._get_connection()
        
        # 创建文档表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建向量表 (使用 BLOB 存储)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_vectors (
                doc_id INTEGER PRIMARY KEY,
                embedding BLOB NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)
        
        # 创建关联表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_doc_id INTEGER NOT NULL,
                target_doc_id INTEGER NOT NULL,
                connection_type TEXT DEFAULT 'related',
                strength REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_doc_id) REFERENCES documents(id),
                FOREIGN KEY (target_doc_id) REFERENCES documents(id),
                UNIQUE(source_doc_id, target_doc_id)
            )
        """)
        
        conn.commit()
        
        # 创建记忆文件目录结构
        (self.memory_dir / "files").mkdir(exist_ok=True)
        
        print(f"✅ 数据库初始化完成: {self.db_path}")
        print(f"✅ 记忆文件目录: {self.memory_dir / 'files'}")
        print("\n🎉 本地记忆系统初始化完成!")
        
    def _compute_hash(self, content: str) -> str:
        """
        计算内容哈希
        
        使用SHA256算法，取前16位作为内容指纹，
        用于检测文件变更和去重。
        
        Args:
            content: 文本内容
            
        Returns:
            str: SHA256哈希值（前16位）
        """
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        获取文本的嵌入向量
        
        使用MiniLM模型将文本转换为384维向量。
        
        Args:
            text: 输入文本
            
        Returns:
            np.ndarray: 384维float32向量
            
        Example:
            >>> embedding = memory._get_embedding("Hello world")
            >>> embedding.shape
            (384,)
        """
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        计算余弦相似度
        
        计算两个向量之间的余弦相似度，范围[-1, 1]，
        通常用于比较文档相似度，结果通常在[0, 1]之间。
        
        Args:
            a: 第一个向量
            b: 第二个向量
            
        Returns:
            float: 余弦相似度值
            
        Note:
            similarity = dot(a, b) / (||a|| * ||b||)
        """
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def index_file(self, file_path: str, content: str = None) -> None:
        """
        索引文件到记忆系统
        
        将文件内容索引到向量数据库，包括：
        1. 读取文件内容
        2. 计算内容哈希
        3. 检查是否已存在且未变更
        4. 生成嵌入向量
        5. 存储到数据库
        
        Args:
            file_path: 文件路径
            content: 文件内容（如不传则读取文件）
            
        Example:
            >>> memory.index_file("my_notes.md")
            >>> memory.index_file("virtual.txt", content="预设内容")
            
        Note:
            - 重复索引同一文件会更新而非创建新记录
            - 使用内容哈希检测文件变更
        """
        conn = self._get_connection()
        file_path = os.path.abspath(file_path)
        
        # 读取文件内容
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"❌ 读取文件失败: {file_path} - {e}")
                return
        
        # 计算内容哈希
        content_hash = self._compute_hash(content)
        
        # 检查文件是否已存在且未更改
        cursor = conn.execute(
            "SELECT id, content_hash FROM documents WHERE file_path = ?",
            (file_path,)
        )
        existing = cursor.fetchone()
        
        if existing:
            doc_id, old_hash = existing
            if old_hash == content_hash:
                print(f"⏭️  文件未更改，跳过: {file_path}")
                return
            # 更新现有文档
            conn.execute(
                "UPDATE documents SET content = ?, content_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (content, content_hash, doc_id)
            )
            # 删除旧向量
            conn.execute("DELETE FROM document_vectors WHERE doc_id = ?", (doc_id,))
            print(f"🔄 更新文件索引: {file_path}")
        else:
            # 插入新文档
            cursor = conn.execute(
                "INSERT INTO documents (file_path, content, content_hash) VALUES (?, ?, ?)",
                (file_path, content, content_hash)
            )
            doc_id = cursor.lastrowid
            print(f"✅ 新增文件索引: {file_path}")
        
        # 生成并存储嵌入向量
        print("🔄 正在生成嵌入向量...")
        embedding = self._get_embedding(content)
        
        # 将 numpy 数组转换为 bytes 存储
        embedding_bytes = embedding.astype(np.float32).tobytes()
        conn.execute(
            "INSERT INTO document_vectors (doc_id, embedding) VALUES (?, ?)",
            (doc_id, embedding_bytes)
        )
        
        conn.commit()
        print(f"✅ 索引完成 (文档ID: {doc_id})")
        
    def search(self, query: str, top_k: int = 5, use_vector: bool = True) -> List[Dict]:
        """
        搜索记忆
        
        根据查询搜索相关文档，支持语义向量搜索和关键词搜索两种模式。
        
        Args:
            query: 搜索查询字符串
            top_k: 返回结果数量，默认5
            use_vector: 是否使用向量搜索（True=语义搜索，False=关键词搜索）
            
        Returns:
            List[Dict]: 搜索结果列表，每个结果包含：
                - id: 文档ID
                - file_path: 文件路径
                - content_preview: 内容预览（前500字符）
                - updated_at: 更新时间
                - similarity: 相似度分数（向量搜索时）
                - match_type: 匹配类型（'vector' 或 'keyword'）
                
        Example:
            >>> # 语义搜索
            >>> results = memory.search("Python async programming", top_k=3)
            >>> 
            >>> # 关键词搜索
            >>> results = memory.search("todo list", use_vector=False)
        """
        conn = self._get_connection()
        
        if use_vector:
            # 向量搜索
            print(f"🔍 执行向量搜索: '{query}'")
            query_embedding = self._get_embedding(query)
            
            # 获取所有文档向量并计算相似度
            cursor = conn.execute("""
                SELECT d.id, d.file_path, d.content, d.updated_at, v.embedding
                FROM documents d
                JOIN document_vectors v ON d.id = v.doc_id
            """)
            
            results = []
            for row in cursor.fetchall():
                doc_id, file_path, content, updated_at, embedding_bytes = row
                
                # 从 bytes 恢复 numpy 数组
                doc_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                
                # 计算余弦相似度
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                
                results.append({
                    'id': doc_id,
                    'file_path': file_path,
                    'content_preview': content[:500] + '...' if len(content) > 500 else content,
                    'updated_at': updated_at,
                    'similarity': float(similarity),
                    'match_type': 'vector'
                })
            
            # 按相似度排序
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
        else:
            # 关键词搜索
            print(f"🔍 执行关键词搜索: '{query}'")
            cursor = conn.execute("""
                SELECT d.id, d.file_path, d.content, d.updated_at
                FROM documents d
                WHERE d.content LIKE ?
                LIMIT ?
            """, (f'%{query}%', top_k))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'file_path': row[1],
                    'content_preview': row[2][:500] + '...' if len(row[2]) > 500 else row[2],
                    'updated_at': row[3],
                    'match_type': 'keyword'
                })
            
            return results
    
    def find_related(self, doc_id: int, top_k: int = 5) -> List[Dict]:
        """
        查找相关文档
        
        基于向量相似度，查找与指定文档最相关的其他文档。
        
        Args:
            doc_id: 源文档ID
            top_k: 返回结果数量，默认5
            
        Returns:
            List[Dict]: 相关文档列表，每个结果包含：
                - id: 文档ID
                - file_path: 文件路径
                - content_preview: 内容预览
                - similarity: 相似度分数
                
        Example:
            >>> # 查找与文档1相关的文档
            >>> related = memory.find_related(1, top_k=3)
            >>> for r in related:
            ...     print(f"相关: {r['file_path']} ({r['similarity']:.2f})")
            
        Note:
            源文档不会出现在结果中
        """
        conn = self._get_connection()
        
        # 获取文档的嵌入向量
        cursor = conn.execute(
            "SELECT embedding FROM document_vectors WHERE doc_id = ?",
            (doc_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            print(f"❌ 文档不存在: {doc_id}")
            return []
        
        print(f"🔗 查找与文档 {doc_id} 相关的文档...")
        
        # 从 bytes 恢复 numpy 数组
        source_embedding = np.frombuffer(row[0], dtype=np.float32)
        
        # 获取所有其他文档的向量并计算相似度
        cursor = conn.execute("""
            SELECT d.id, d.file_path, d.content, v.embedding
            FROM documents d
            JOIN document_vectors v ON d.id = v.doc_id
            WHERE d.id != ?
        """, (doc_id,))
        
        results = []
        for r in cursor.fetchall():
            target_id, file_path, content, embedding_bytes = r
            target_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            similarity = self._cosine_similarity(source_embedding, target_embedding)
            
            results.append({
                'id': target_id,
                'file_path': file_path,
                'content_preview': content[:300] + '...' if len(content) > 300 else content,
                'similarity': float(similarity)
            })
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def list_documents(self) -> List[Dict]:
        """
        列出所有文档
        
        Returns:
            List[Dict]: 文档列表，每个文档包含：
                - id: 文档ID
                - file_path: 文件路径
                - updated_at: 更新时间
                - size: 内容大小（字节）
                
        Example:
            >>> docs = memory.list_documents()
            >>> for doc in docs:
            ...     print(f"ID {doc['id']}: {doc['file_path']}")
        """
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT id, file_path, updated_at, LENGTH(content) as size
            FROM documents
            ORDER BY updated_at DESC
        """)
        
        return [{
            'id': row[0],
            'file_path': row[1],
            'updated_at': row[2],
            'size': row[3]
        } for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """
        获取系统统计信息
        
        Returns:
            Dict: 统计信息，包含：
                - document_count: 文档数量
                - vector_count: 向量数量
                - db_size: 数据库文件大小（字节）
                - total_size: 总占用空间（字节）
                
        Example:
            >>> stats = memory.get_stats()
            >>> print(f"文档数: {stats['document_count']}")
            >>> print(f"存储: {stats['total_size'] / 1024:.2f} KB")
        """
        conn = self._get_connection()
        
        stats = {}
        
        # 文档数量
        cursor = conn.execute("SELECT COUNT(*) FROM documents")
        stats['document_count'] = cursor.fetchone()[0]
        
        # 向量数量
        cursor = conn.execute("SELECT COUNT(*) FROM document_vectors")
        stats['vector_count'] = cursor.fetchone()[0]
        
        # 数据库大小
        stats['db_size'] = os.path.getsize(self.db_path)
        
        # 记忆目录大小
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.memory_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        stats['total_size'] = total_size
        
        return stats
    
    def delete_document(self, doc_id: int) -> None:
        """
        删除文档
        
        删除指定文档及其向量，关联关系也会被删除。
        
        Args:
            doc_id: 要删除的文档ID
            
        Example:
            >>> memory.delete_document(1)
            ✅ 已删除文档 1
        """
        conn = self._get_connection()
        
        # 删除向量
        conn.execute("DELETE FROM document_vectors WHERE doc_id = ?", (doc_id,))
        
        # 删除关联
        conn.execute("DELETE FROM connections WHERE source_doc_id = ? OR target_doc_id = ?", 
                    (doc_id, doc_id))
        
        # 删除文档
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        
        conn.commit()
        print(f"✅ 已删除文档 {doc_id}")


def main():
    """
    命令行入口点
    
    提供CLI接口用于初始化、索引、搜索等操作。
    
    Usage:
        python local_memory.py init                    # 初始化系统
        python local_memory.py index note.txt          # 索引文件
        python local_memory.py search "query"          # 搜索
        python local_memory.py related 1               # 查找相关文档
        python local_memory.py list                    # 列出所有文档
        python local_memory.py stats                   # 系统统计
    """
    parser = argparse.ArgumentParser(
        description='本地记忆系统 - SQLite + MiniLM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python local_memory.py init                    # 初始化系统
  python local_memory.py index note.txt          # 索引文件
  python local_memory.py search "query"          # 搜索
  python local_memory.py related 1               # 查找相关文档
  python local_memory.py list                    # 列出所有文档
  python local_memory.py stats                   # 系统统计
        """
    )
    
    parser.add_argument('--memory-dir', help='记忆存储目录', default=None)
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init 命令
    subparsers.add_parser('init', help='初始化记忆系统')
    
    # index 命令
    index_parser = subparsers.add_parser('index', help='索引文件')
    index_parser.add_argument('file', help='要索引的文件路径')
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索记忆')
    search_parser.add_argument('query', help='搜索查询')
    search_parser.add_argument('-k', '--top-k', type=int, default=5, help='返回结果数量')
    search_parser.add_argument('--keyword', action='store_true', help='使用关键词搜索而非向量搜索')
    
    # related 命令
    related_parser = subparsers.add_parser('related', help='查找相关文档')
    related_parser.add_argument('doc_id', type=int, help='文档ID')
    related_parser.add_argument('-k', '--top-k', type=int, default=5, help='返回结果数量')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有文档')
    
    # stats 命令
    subparsers.add_parser('stats', help='显示系统统计信息')
    
    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除文档')
    delete_parser.add_argument('doc_id', type=int, help='要删除的文档ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    memory = LocalMemorySystem(args.memory_dir)
    
    if args.command == 'init':
        memory.init()
    
    elif args.command == 'index':
        memory.index_file(args.file)
    
    elif args.command == 'search':
        results = memory.search(args.query, args.top_k, not args.keyword)
        print(f"\n📊 找到 {len(results)} 个结果:\n")
        for i, r in enumerate(results, 1):
            print(f"[{i}] {r['file_path']}")
            print(f"    类型: {r['match_type']}")
            if 'similarity' in r:
                print(f"    相似度: {r['similarity']:.4f}")
            print(f"    更新: {r['updated_at']}")
            print(f"    预览: {r['content_preview'][:200]}...")
            print()
    
    elif args.command == 'related':
        results = memory.find_related(args.doc_id, args.top_k)
        print(f"\n📊 找到 {len(results)} 个相关文档:\n")
        for i, r in enumerate(results, 1):
            print(f"[{i}] ID: {r['id']} - {r['file_path']}")
            print(f"    相似度: {r['similarity']:.4f}")
            print(f"    预览: {r['content_preview'][:200]}...")
            print()
    
    elif args.command == 'list':
        docs = memory.list_documents()
        print(f"\n📄 共 {len(docs)} 个文档:\n")
        for d in docs:
            print(f"  ID: {d['id']} | {d['file_path']}")
            print(f"      大小: {d['size']} bytes | 更新: {d['updated_at']}")
        print()
    
    elif args.command == 'stats':
        stats = memory.get_stats()
        print("\n📊 系统统计信息:\n")
        print(f"  文档数量: {stats['document_count']}")
        print(f"  向量数量: {stats['vector_count']}")
        print(f"  数据库大小: {stats['db_size'] / 1024:.2f} KB")
        print(f"  总占用空间: {stats['total_size'] / 1024:.2f} KB")
        print()
    
    elif args.command == 'delete':
        memory.delete_document(args.doc_id)


if __name__ == '__main__':
    main()
