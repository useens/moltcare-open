#!/usr/bin/env python3
"""
记忆系统适配器 - 集成向量记忆到现有系统
兼容旧的 memory_search 接口
"""

import os
import sys
from pathlib import Path

# 确保可以导入 core 模块
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from core.vector_memory import create_memory_system

class VectorMemoryAdapter:
    """
    向量记忆适配器
    提供与旧版 memory_search 兼容的接口
    """
    
    _instance = None
    _memory = None
    
    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_memory(db_path)
            cls._instance._init_cache()  # 初始化缓存
        return cls._instance
    
    def _init_cache(self):
        """初始化查询缓存"""
        self._cache = {}  # 缓存字典: {hash: (results, timestamp)}
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_max_size = 100  # 最大缓存条目
        self._cache_ttl_seconds = 3600  # 缓存过期时间: 1小时
    
    def _init_memory(self, db_path=None):
        """初始化向量记忆系统"""
        from pathlib import Path
        if db_path is None:
            db_path = os.path.expanduser("~/.openclaw/workspace/memory/vector/production")
        
        db_path = Path(db_path)
        os.makedirs(db_path, exist_ok=True)
        
        try:
            # 创建配置，禁用自动导入和优化
            from core.vector_memory import MemoryConfig
            config = MemoryConfig(
                db_path=db_path,
                model_name="BAAI/bge-large-zh-v1.5",
                embedding_dim=1024,
                table_name="memories",
                auto_import_on_start=False,  # 禁用自动导入
                enable_auto_cleanup=False,
            )
            from core.vector_memory import MemoryManager
            self._memory = MemoryManager(config)
            print(f"✅ 向量记忆系统已加载: {db_path}")
        except Exception as e:
            print(f"⚠️ 向量记忆加载失败: {e}")
            import traceback
            traceback.print_exc()
            self._memory = None
    
    def _get_cache_key(self, query: str, top_k: int) -> str:
        """生成缓存键"""
        import hashlib
        key_str = f"{query}:{top_k}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """检查缓存是否过期"""
        import time
        return (time.time() - timestamp) < self._cache_ttl_seconds
    
    def _cleanup_cache(self):
        """清理过期和超出限制的缓存"""
        import time
        current_time = time.time()
        
        # 移除过期项
        expired_keys = [
            k for k, (_, ts) in self._cache.items() 
            if (current_time - ts) > self._cache_ttl_seconds
        ]
        for k in expired_keys:
            del self._cache[k]
        
        # 如果仍然超出限制，移除最早的项
        if len(self._cache) > self._cache_max_size:
            # 按时间戳排序，移除最早的
            sorted_items = sorted(self._cache.items(), key=lambda x: x[1][1])
            to_remove = len(self._cache) - self._cache_max_size
            for i in range(to_remove):
                del self._cache[sorted_items[i][0]]
    
    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": f"{hit_rate:.1%}",
            "cached_items": len(self._cache),
            "max_size": self._cache_max_size,
            "ttl_seconds": self._cache_ttl_seconds,
        }
    
    def search(self, query: str, top_k: int = 5, **kwargs):
        """
        语义搜索记忆（带缓存）
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if self._memory is None:
            print("⚠️ 向量记忆未初始化，返回空结果")
            return []
        
        # 检查缓存
        cache_key = self._get_cache_key(query, top_k)
        if cache_key in self._cache:
            results, timestamp = self._cache[cache_key]
            if self._is_cache_valid(timestamp):
                self._cache_hits += 1
                return results
        
        # 缓存未命中，执行搜索
        self._cache_misses += 1
        
        try:
            results = self._memory.search(query, top_k=top_k)
            formatted_results = [
                {
                    "content": r.content if hasattr(r, 'content') else str(r),
                    "metadata": r.metadata if hasattr(r, 'metadata') else {},
                    "score": r.score if hasattr(r, 'score') else 0.0,
                }
                for r in results
            ]
            
            # 存入缓存
            import time
            self._cache[cache_key] = (formatted_results, time.time())
            self._cleanup_cache()
            
            return formatted_results
        except Exception as e:
            print(f"⚠️ 搜索失败: {e}")
            return []
    
    def add_memory(self, content: str, metadata: dict = None):
        """
        添加记忆
        
        Args:
            content: 记忆内容
            metadata: 元数据
        """
        if self._memory is None:
            return
        
        try:
            self._memory.add_memory(content, metadata=metadata or {})
        except Exception as e:
            print(f"⚠️ 添加记忆失败: {e}")
    
    def close(self):
        """关闭连接"""
        if self._memory:
            self._memory.close()
            self._memory = None


# 全局适配器实例（预加载，常驻内存）
_memory_adapter = None

def get_memory_adapter(db_path=None, force_reload=False):
    """获取记忆适配器单例
    
    Args:
        db_path: 数据库路径
        force_reload: 是否强制重新加载
    """
    global _memory_adapter
    if _memory_adapter is None or force_reload:
        _memory_adapter = VectorMemoryAdapter(db_path)
    return _memory_adapter

# 预加载模型到内存（常驻）
def _preload_model():
    """模块导入时预加载模型"""
    import os
    db_path = os.path.expanduser("~/.openclaw/workspace/memory/vector/production")
    print("🔄 正在预加载向量记忆模型（常驻内存）...")
    adapter = get_memory_adapter(db_path)
    if adapter._memory:
        print("✅ 模型已常驻内存，查询延迟降至 ~250ms")
    return adapter

# 模块导入时自动预加载
_memory_adapter = _preload_model()


def memory_search(query: str, top_k: int = 5, **kwargs):
    """
    记忆搜索函数（兼容旧接口）
    
    用法:
        from memory_adapter import memory_search
        results = memory_search("用户偏好")
    """
    adapter = get_memory_adapter()
    return adapter.search(query, top_k=top_k, **kwargs)


# 向后兼容
if __name__ == "__main__":
    # 测试
    print("测试记忆适配器...")
    
    adapter = get_memory_adapter()
    
    # 添加测试数据
    adapter.add_memory("测试记忆内容", {"source": "test"})
    
    # 搜索
    results = adapter.search("测试")
    print(f"找到 {len(results)} 条结果")
    
    for r in results:
        print(f"  - {r['content'][:50]}...")
    
    adapter.close()
    print("✅ 测试完成")
