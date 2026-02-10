"""
向量记忆系统 - 统一API入口

提供简洁的接口用于记忆存储、搜索和管理。
"""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# 主要类导入
from .embedder import Embedder, TextChunker, EmbeddingConfig
from .vector_store import VectorStore, VectorRecord
from .memory_search import MemorySearch, SearchResult, SearchConfig
from .memory_manager import MemoryManager, MemoryConfig

# 版本信息
__version__ = "1.0.0"
__all__ = [
    # 主类
    "MemoryManager",
    "MemorySearch", 
    "VectorStore",
    "Embedder",
    # 配置类
    "MemoryConfig",
    "SearchConfig",
    "EmbeddingConfig",
    # 数据类
    "VectorRecord",
    "SearchResult",
    "TextChunker",
    # 便捷函数
    "create_memory_system",
]


def create_memory_system(
    db_path: Union[str, Path],
    model_name: str = "BAAI/bge-large-zh-v1.5",
    embedding_dim: int = 1024,
    table_name: str = "memories",
) -> MemoryManager:
    """
    创建并初始化一个完整的向量记忆系统。
    
    这是一个便捷函数，用于快速创建配置好的记忆管理系统。
    
    Args:
        db_path: LanceDB数据库路径
        model_name: 使用的嵌入模型名称
        embedding_dim: 嵌入向量维度
        table_name: 数据表名称
        
    Returns:
        配置好的MemoryManager实例
        
    Example:
        >>> memory = create_memory_system("./memory_db")
        >>> memory.add_memory("这是一段需要记忆的内容")
        >>> results = memory.search("相关内容查询")
    """
    config = MemoryConfig(
        db_path=Path(db_path),
        model_name=model_name,
        embedding_dim=embedding_dim,
        table_name=table_name,
    )
    return MemoryManager(config)
