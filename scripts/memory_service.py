#!/usr/bin/env python3
"""
Memory Service - 统一记忆服务层
Phase 1-3 优化实现
"""
import os
import sys
import json
import sqlite3
import hashlib
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import lru_cache
import numpy as np

# 添加路径
sys.path.insert(0, "/root/.openclaw/workspace/local-memory-system")

# 全局模型实例（Phase 1: 模型常驻）
_model = None
_model_lock = threading.Lock()

def get_embedding_model():
    """获取或创建嵌入模型（单例模式）"""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                print("🔄 预加载MiniLM模型...")
                _model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ 模型常驻内存完成")
    return _model

# 连接池（Phase 2: 连接池）
class ConnectionPool:
    """SQLite连接池"""
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool = []
        self._lock = threading.Lock()
        
        # 预创建连接
        for _ in range(max_connections):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")  # 支持并发
            self._pool.append(conn)
    
    def get_connection(self):
        """获取连接"""
        with self._lock:
            if self._pool:
                return self._pool.pop()
            # 如果没有可用连接，创建新连接
            return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def release_connection(self, conn):
        """释放连接"""
        with self._lock:
            if len(self._pool) < self.max_connections:
                self._pool.append(conn)
            else:
                conn.close()

class MemoryService:
    """统一记忆服务（Phase 2: 统一抽象层）"""
    
    def __init__(self, memory_dir: str = None):
        self.memory_dir = Path(memory_dir or "/root/.openclaw/workspace/data/vector_memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.memory_dir / "memory.db"
        self.pool = ConnectionPool(str(self.db_path))
        
        # 确保模型已加载
        self.model = get_embedding_model()
        
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = self.pool.get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    signal INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_vectors (
                    doc_id INTEGER PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (doc_id) REFERENCES documents(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_stats (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            self.pool.release_connection(conn)
    
    def index_content(self, content: str, source: str, signal: int = None) -> Dict:
        """索引内容到记忆系统"""
        if signal is None:
            signal = self._estimate_signal(content)
        
        # Signal < 8 跳过
        if signal < 8:
            return {"success": False, "reason": f"Signal {signal} < 8"}
        
        # 创建临时文件
        source_hash = hashlib.sha256(source.encode()).hexdigest()[:16]
        temp_file = self.memory_dir / "realtime" / f"{source_hash}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        temp_file.parent.mkdir(exist_ok=True)
        
        metadata = f"""---
source: {source}
signal: {signal}
indexed_at: {datetime.now().isoformat()}
---

"""
        temp_file.write_text(metadata + content, encoding="utf-8")
        
        # 索引到数据库
        conn = self.pool.get_connection()
        try:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # 检查是否已存在
            cursor = conn.execute(
                "SELECT id FROM documents WHERE content_hash = ?",
                (content_hash,)
            )
            if cursor.fetchone():
                return {"success": False, "reason": "Content already indexed"}
            
            # 插入文档
            cursor = conn.execute(
                "INSERT INTO documents (file_path, content, content_hash, signal) VALUES (?, ?, ?, ?)",
                (str(temp_file), content, content_hash, signal)
            )
            doc_id = cursor.lastrowid
            
            # 生成向量
            embedding = self.model.encode(content, convert_to_numpy=True)
            embedding_bytes = embedding.astype(np.float32).tobytes()
            
            conn.execute(
                "INSERT INTO document_vectors (doc_id, embedding) VALUES (?, ?)",
                (doc_id, embedding_bytes)
            )
            conn.commit()
            
            return {"success": True, "doc_id": doc_id, "signal": signal}
            
        finally:
            self.pool.release_connection(conn)
    
    @lru_cache(maxsize=100)  # Phase 2: LRU缓存
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """语义搜索（带缓存）"""
        query_vec = self.model.encode(query, convert_to_numpy=True)
        
        conn = self.pool.get_connection()
        try:
            cursor = conn.execute("SELECT doc_id, embedding FROM document_vectors")
            results = []
            
            for doc_id, embedding_bytes in cursor:
                doc_vec = np.frombuffer(embedding_bytes, dtype=np.float32)
                similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
                
                # 获取文档信息
                doc_cursor = conn.execute(
                    "SELECT file_path, content, signal FROM documents WHERE id = ?",
                    (doc_id,)
                )
                row = doc_cursor.fetchone()
                if row:
                    results.append({
                        "doc_id": doc_id,
                        "file_path": row[0],
                        "content_preview": row[1][:200],
                        "signal": row[2],
                        "similarity": float(similarity)
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
            
        finally:
            self.pool.release_connection(conn)
    
    def _estimate_signal(self, content: str) -> int:
        """估算Signal等级"""
        score = 5
        keywords = ["关键", "重要", "紧急", "必须", "核心", "critical", "important", "安全", "风险"]
        for kw in keywords:
            if kw in content.lower():
                score += 1
        if "```" in content or "def " in content:
            score += 2
        return min(10, score)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        conn = self.pool.get_connection()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM document_vectors")
            vec_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT AVG(signal) FROM documents")
            avg_signal = cursor.fetchone()[0] or 0
            
            return {
                "documents": doc_count,
                "vectors": vec_count,
                "avg_signal": round(avg_signal, 2),
                "model_cached": _model is not None
            }
        finally:
            self.pool.release_connection(conn)
    
    def backup(self, backup_dir: str = None) -> str:
        """备份数据库（Phase 3: 自动备份）"""
        if backup_dir is None:
            backup_dir = self.memory_dir / "backups"
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"memory_backup_{timestamp}.db"
        
        import shutil
        shutil.copy2(self.db_path, backup_file)
        
        # 清理旧备份（保留7天）
        self._cleanup_old_backups(backup_path, days=7)
        
        return str(backup_file)
    
    def _cleanup_old_backups(self, backup_path: Path, days: int = 7):
        """清理旧备份"""
        cutoff = datetime.now() - timedelta(days=days)
        for f in backup_path.glob("memory_backup_*.db"):
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
                print(f"🗑️  删除旧备份: {f.name}")

# 全局服务实例
_memory_service = None

def get_memory_service() -> MemoryService:
    """获取记忆服务单例"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service

if __name__ == "__main__":
    # 测试
    service = get_memory_service()
    print("📊 初始统计:", service.get_stats())
    
    # 测试索引
    result = service.index_content("测试关键内容", "test")
    print("📝 索引结果:", result)
    
    # 测试搜索
    results = service.search("测试")
    print("🔍 搜索结果:", len(results))
    
    print("📊 最终统计:", service.get_stats())
