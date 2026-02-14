"""
LanceDB向量存储封装模块

提供向量数据库的初始化、CRUD操作和相似度搜索功能。
"""

import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

import lancedb
import numpy as np
import pyarrow as pa

logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    """向量记录数据类"""
    
    id: str
    vector: np.ndarray
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "vector": self.vector,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorRecord":
        """从字典创建实例"""
        return cls(
            id=data["id"],
            vector=np.array(data["vector"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now()),
            updated_at=data.get("updated_at", datetime.now()),
        )


class VectorStore:
    """
    LanceDB向量存储封装类
    
    提供向量数据的存储、检索和管理功能。
    
    Attributes:
        db_path: 数据库文件路径
        table_name: 数据表名称
        embedding_dim: 嵌入向量维度
        db: LanceDB连接实例
        table: 数据表实例
    """
    
    def __init__(
        self,
        db_path: Union[str, Path],
        table_name: str = "memories",
        embedding_dim: int = 384,
    ):
        """
        初始化向量存储
        
        Args:
            db_path: LanceDB数据库路径
            table_name: 数据表名称
            embedding_dim: 嵌入向量维度
        """
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.embedding_dim = embedding_dim
        self.db: Optional[lancedb.DBConnection] = None
        self.table: Optional[lancedb.Table] = None
        self._initialized = False
        
    def initialize(self) -> "VectorStore":
        """
        初始化数据库连接和数据表
        
        Returns:
            self: 支持链式调用
        """
        if self._initialized:
            return self
            
        try:
            # 确保目录存在
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 连接数据库
            self.db = lancedb.connect(str(self.db_path))
            
            # 检查或创建表
            if self.table_name in self.db.table_names():
                self.table = self.db.open_table(self.table_name)
                logger.info(f"已打开现有表: {self.table_name}")
            else:
                self.table = self._create_table()
                logger.info(f"已创建新表: {self.table_name}")
                
            self._initialized = True
            
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            raise
            
        return self
    
    def _create_table(self) -> lancedb.Table:
        """
        创建向量数据表
        
        Returns:
            LanceDB表实例
        """
        schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), self.embedding_dim)),
            pa.field("content", pa.string()),
            pa.field("metadata", pa.string()),  # JSON字符串存储
            pa.field("created_at", pa.timestamp("us")),
            pa.field("updated_at", pa.timestamp("us")),
        ])
        
        table = self.db.create_table(self.table_name, schema=schema)
        
        # 注意：LanceDB 需要在有数据后才能创建索引
        # 索引将在第一批数据添加后延迟创建
        self._index_needs_creation = True
        
        return table
    
    def add(
        self,
        vector: np.ndarray,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        record_id: Optional[str] = None,
    ) -> str:
        """
        添加单条向量记录
        
        Args:
            vector: 嵌入向量
            content: 原始文本内容
            metadata: 元数据字典
            record_id: 记录ID（自动生成UUID）
            
        Returns:
            记录ID
        """
        self._ensure_initialized()
        
        record_id = record_id or str(uuid.uuid4())
        now = datetime.now()
        
        # 确保向量是float32类型
        vector = np.array(vector, dtype=np.float32)
        
        # 序列化metadata
        import json
        metadata_str = json.dumps(metadata or {})
        
        data = [{
            "id": record_id,
            "vector": vector.tolist(),
            "content": content,
            "metadata": metadata_str,
            "created_at": now,
            "updated_at": now,
        }]
        
        self.table.add(data)
        logger.debug(f"已添加记录: {record_id}")
        
        # 延迟创建索引（首次添加数据时）
        if getattr(self, '_index_needs_creation', False):
            try:
                self.table.create_index(
                    metric="cosine",
                    num_partitions=min(256, max(1, self.table.count_rows() // 1000)),
                    num_sub_vectors=self.embedding_dim // 8,
                )
                self._index_needs_creation = False
                logger.info("向量索引创建成功")
            except Exception as e:
                logger.warning(f"索引创建失败（将在更多数据后重试）: {e}")
        
        return record_id
    
    def add_batch(
        self,
        records: List[Tuple[np.ndarray, str, Optional[Dict[str, Any]]]],
    ) -> List[str]:
        """
        批量添加向量记录
        
        Args:
            records: 记录列表，每项为 (vector, content, metadata) 元组
            
        Returns:
            记录ID列表
        """
        self._ensure_initialized()
        
        import json
        now = datetime.now()
        data = []
        record_ids = []
        
        for vector, content, metadata in records:
            record_id = str(uuid.uuid4())
            record_ids.append(record_id)
            
            vector = np.array(vector, dtype=np.float32)
            metadata_str = json.dumps(metadata or {})
            
            data.append({
                "id": record_id,
                "vector": vector.tolist(),
                "content": content,
                "metadata": metadata_str,
                "created_at": now,
                "updated_at": now,
            })
        
        self.table.add(data)
        logger.debug(f"已批量添加 {len(data)} 条记录")
        
        # 延迟创建索引（首次添加数据时）
        if getattr(self, '_index_needs_creation', False):
            try:
                self.table.create_index(
                    metric="cosine",
                    num_partitions=min(256, max(1, self.table.count_rows() // 1000)),
                    num_sub_vectors=self.embedding_dim // 8,
                )
                self._index_needs_creation = False
                logger.info("向量索引创建成功")
            except Exception as e:
                logger.warning(f"索引创建失败（将在更多数据后重试）: {e}")
        
        return record_ids
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filter_expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        相似度搜索
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_expr: 过滤条件表达式
            
        Returns:
            搜索结果列表，每项包含记录信息和相似度分数
        """
        self._ensure_initialized()
        
        query_vector = np.array(query_vector, dtype=np.float32)
        
        search = self.table.search(query_vector.tolist())
        
        if filter_expr:
            search = search.where(filter_expr)
        
        results = search.limit(top_k).to_list()
        
        # 解析metadata
        import json
        for r in results:
            r["metadata"] = json.loads(r.get("metadata", "{}"))
            r["score"] = r.get("_distance", 0.0)
        
        return results
    
    def delete(self, record_id: str) -> bool:
        """
        删除记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否删除成功
        """
        self._ensure_initialized()
        
        try:
            self.table.delete(f"id = '{record_id}'")
            logger.debug(f"已删除记录: {record_id}")
            return True
        except Exception as e:
            logger.error(f"删除记录失败 {record_id}: {e}")
            return False
    
    def update(
        self,
        record_id: str,
        vector: Optional[np.ndarray] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        更新记录
        
        Args:
            record_id: 记录ID
            vector: 新向量（可选）
            content: 新内容（可选）
            metadata: 新元数据（可选，会合并到现有元数据）
            
        Returns:
            是否更新成功
        """
        self._ensure_initialized()
        
        try:
            # 获取现有记录
            existing = self.table.to_pandas()
            existing = existing[existing["id"] == record_id]
            
            if existing.empty:
                logger.warning(f"记录不存在: {record_id}")
                return False
            
            row = existing.iloc[0]
            import json
            
            # 构建更新数据
            update_data = {
                "id": record_id,
                "vector": vector.tolist() if vector is not None else row["vector"],
                "content": content if content is not None else row["content"],
                "metadata": json.dumps(metadata) if metadata is not None else row["metadata"],
                "updated_at": datetime.now(),
            }
            
            # LanceDB使用add进行更新（upsert）
            self.table.add([update_data], mode="overwrite")
            logger.debug(f"已更新记录: {record_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新记录失败 {record_id}: {e}")
            return False
    
    def get(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单条记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            记录字典，不存在返回None
        """
        self._ensure_initialized()
        
        try:
            results = self.table.to_pandas()
            results = results[results["id"] == record_id]
            
            if results.empty:
                return None
            
            row = results.iloc[0].to_dict()
            import json
            row["metadata"] = json.loads(row.get("metadata", "{}"))
            row["vector"] = np.array(row["vector"])
            
            return row
            
        except Exception as e:
            logger.error(f"获取记录失败 {record_id}: {e}")
            return None
    
    def get_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        获取所有记录
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            记录列表
        """
        self._ensure_initialized()
        
        df = self.table.to_pandas()
        
        if offset > 0:
            df = df.iloc[offset:]
        if limit:
            df = df.head(limit)
        
        import json
        records = []
        for _, row in df.iterrows():
            record = row.to_dict()
            record["metadata"] = json.loads(record.get("metadata", "{}"))
            record["vector"] = np.array(record["vector"])
            records.append(record)
        
        return records
    
    def count(self) -> int:
        """
        获取记录总数
        
        Returns:
            记录数量
        """
        self._ensure_initialized()
        return len(self.table.to_pandas())
    
    def clear(self) -> None:
        """清空所有记录"""
        self._ensure_initialized()
        self.table.delete("true")
        logger.info("已清空所有记录")
    
    def optimize(self) -> None:
        """优化索引和存储"""
        self._ensure_initialized()
        self.table.compact_files()
        self.table.optimize()
        logger.info("索引优化完成")
    
    def _ensure_initialized(self) -> None:
        """确保已初始化"""
        if not self._initialized:
            self.initialize()
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.db:
            # LanceDB不需要显式关闭
            self.db = None
            self.table = None
            self._initialized = False
            logger.info("数据库连接已关闭")
    
    def __enter__(self) -> "VectorStore":
        """上下文管理器入口"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.close()
