#!/usr/bin/env python3
"""
Memory System v5 - 向量记忆核心模块
处理记忆的存储、检索和向量索引
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
VECTOR_DIR = WORKSPACE / "memory" / "vector"
LONG_TERM_FILE = VECTOR_DIR / "long_term_memories.json"
LANCE_DIR = VECTOR_DIR / "production" / "memories.lance"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryCoreV5:
    """向量记忆核心 - 支持JSON长期记忆和Lance向量存储"""
    
    def __init__(self):
        self.storage_dir = VECTOR_DIR
        self.long_term_file = LONG_TERM_FILE
        self.lance_dir = LANCE_DIR
        self.memories = []
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储目录"""
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        (VECTOR_DIR / "production").mkdir(parents=True, exist_ok=True)
        
        # 加载现有长期记忆
        if self.long_term_file.exists():
            try:
                with open(self.long_term_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = list(data.values()) if isinstance(data, dict) else data
                    logger.info(f"已加载 {len(self.memories)} 条长期记忆")
            except Exception as e:
                logger.error(f"加载长期记忆失败: {e}")
                self.memories = []
    
    def add_memory(self, content: str, metadata: Optional[Dict] = None) -> str:
        """
        添加新记忆
        
        Args:
            content: 记忆内容
            metadata: 可选的元数据
            
        Returns:
            记忆ID
        """
        memory_id = hashlib.md5(f"{content}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        memory = {
            "id": memory_id,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "access_count": 0,
            "last_accessed": datetime.now().isoformat()
        }
        
        self.memories.append(memory)
        self._save_long_term()
        
        logger.info(f"添加记忆: {memory_id}")
        return memory_id
    
    def _save_long_term(self):
        """保存到长期记忆文件"""
        try:
            # 转换为字典格式存储
            data = {m["id"]: m for m in self.memories}
            with open(self.long_term_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存长期记忆失败: {e}")
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        语义搜索（支持Lance向量库）
        
        Args:
            query: 搜索查询
            limit: 返回结果数量
            
        Returns:
            匹配的记忆列表
        """
        # 优先尝试Lance向量搜索
        try:
            import lancedb
            from sentence_transformers import SentenceTransformer
            
            db = lancedb.connect(str(self.lance_dir.parent))
            if "memories" in db.table_names():
                table = db.open_table("memories")
                
                # 加载模型并编码查询
                model = SentenceTransformer('all-MiniLM-L6-v2')
                query_vector = model.encode([query])[0]
                
                # 执行向量搜索
                results = table.search(query_vector).limit(limit).to_pandas()
                
                return results.to_dict('records')
        except Exception as e:
            logger.debug(f"Lance搜索失败，回退到关键词搜索: {e}")
        
        # 回退到关键词搜索
        query_lower = query.lower()
        results = []
        
        for memory in self.memories:
            content = memory.get("content", "").lower()
            if query_lower in content:
                results.append(memory)
                memory["access_count"] = memory.get("access_count", 0) + 1
                memory["last_accessed"] = datetime.now().isoformat()
        
        results.sort(key=lambda x: (x.get("access_count", 0), x.get("timestamp", "")), reverse=True)
        return results[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        return {
            "total_memories": len(self.memories),
            "long_term_file": str(self.long_term_file),
            "lance_dir": str(self.lance_dir),
            "lance_exists": self.lance_dir.exists(),
            "last_updated": datetime.now().isoformat()
        }
    
    def rebuild_index(self):
        """重建向量索引（预留接口）"""
        logger.info("向量索引重建功能待实现（需要lance库）")
        logger.info(f"当前长期记忆数: {len(self.memories)}")


# 兼容性接口
def get_memory_core() -> MemoryCoreV5:
    """获取记忆核心实例（单例模式）"""
    if not hasattr(get_memory_core, "_instance"):
        get_memory_core._instance = MemoryCoreV5()
    return get_memory_core._instance


if __name__ == "__main__":
    # 测试
    core = MemoryCoreV5()
    print(f"记忆统计: {core.get_stats()}")
