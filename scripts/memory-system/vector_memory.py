#!/usr/bin/env python3
"""
向量记忆系统 v5.2 - 语义检索核心 (简化版)
使用MiniLM + numpy实现，避免架构兼容问题
"""

import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pickle

# 路径配置
WORKSPACE = Path("/root/.openclaw/workspace")
VECTOR_DIR = WORKSPACE / "memory/vector"
VECTOR_FILE = VECTOR_DIR / "memory_vectors.pkl"

class VectorMemorySystem:
    """向量记忆系统 - v5.2核心"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """初始化向量记忆系统"""
        from sentence_transformers import SentenceTransformer
        
        self.model = SentenceTransformer(model_name)
        self.vector_file = VECTOR_FILE
        
        # 确保目录存在
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        
        # 加载现有记忆
        self.memories = self._load_vectors()
        
    def _get_embedding(self, text: str) -> np.ndarray:
        """获取文本的向量嵌入"""
        return self.model.encode(text, convert_to_numpy=True)
    
    def _load_vectors(self) -> Dict[str, Dict]:
        """加载向量记忆"""
        if self.vector_file.exists():
            with open(self.vector_file, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_vectors(self):
        """保存向量记忆"""
        with open(self.vector_file, 'wb') as f:
            pickle.dump(self.memories, f)
    
    def add_memory(self, memory_id: str, content: str, source: str = "",
                   memory_type: str = "general", importance: int = 5,
                   tags: List[str] = None) -> bool:
        """添加记忆到向量数据库"""
        try:
            # 生成向量
            embedding = self._get_embedding(content)
            
            self.memories[memory_id] = {
                "id": memory_id,
                "content": content,
                "source": source,
                "type": memory_type,
                "importance": importance,
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
                "embedding": embedding
            }
            
            self._save_vectors()
            return True
            
        except Exception as e:
            print(f"❌ 添加记忆失败: {e}")
            return False
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def search_similar(self, query: str, top_k: int = 5, 
                       min_similarity: float = 0.15) -> List[Dict]:
        """语义相似度搜索"""
        if not self.memories:
            return []
        
        # 生成查询向量
        query_embedding = self._get_embedding(query)
        
        # 计算相似度
        results = []
        for mid, memory in self.memories.items():
            similarity = self._cosine_similarity(query_embedding, memory["embedding"])
            
            if similarity >= min_similarity:
                results.append({
                    "id": mid,
                    "content": memory["content"],
                    "source": memory.get("source", ""),
                    "type": memory.get("type", "general"),
                    "importance": memory.get("importance", 5),
                    "tags": memory.get("tags", []),
                    "similarity": round(float(similarity), 3)
                })
        
        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def migrate_from_json(self, json_file: Path = None) -> int:
        """从JSON文件迁移记忆到向量数据库"""
        if json_file is None:
            json_file = VECTOR_DIR / "long_term_memories.json"
        
        if not json_file.exists():
            print(f"❌ 文件不存在: {json_file}")
            return 0
        
        with open(json_file, 'r', encoding='utf-8') as f:
            memories = json.load(f)
        
        count = 0
        for m in memories:
            success = self.add_memory(
                memory_id=m["id"],
                content=m["content"],
                source=m.get("source", ""),
                memory_type=m.get("type", "general"),
                importance=m.get("importance", 5),
                tags=m.get("tags", [])
            )
            if success:
                count += 1
                print(f"  ✅ 迁移: {m['content'][:50]}...")
        
        return count
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_memories": len(self.memories),
            "vector_file": str(self.vector_file),
            "model": "all-MiniLM-L6-v2",
            "embedding_dim": 384
        }


# 便捷函数
def get_vector_memory() -> VectorMemorySystem:
    """获取向量记忆系统单例"""
    return VectorMemorySystem()


def test_vector_search():
    """测试向量搜索"""
    print("🧪 测试向量记忆系统 v5.2")
    print("=" * 50)
    
    vms = get_vector_memory()
    
    # 添加测试记忆
    test_memories = [
        ("1", "v5.1记忆系统重构完成，分层架构实现"),
        ("2", "多代理并行测试成功，VM协作正常"),
        ("3", "深度学习闭环：Signal>7自动深度提取"),
        ("4", "双节点架构：主节点+VM智能分工"),
        ("5", "用户zxl授权v5.2自主开发，不再请示"),
    ]
    
    for mid, content in test_memories:
        vms.add_memory(mid, content, importance=8)
    
    # 测试语义搜索
    queries = [
        "记忆优化",  # 应该匹配"记忆系统重构"
        "VM协作",     # 应该匹配"VM协作"和"双节点"
        "用户指令",   # 应该匹配"zxl授权"
    ]
    
    for query in queries:
        print(f"\n🔍 查询: '{query}'")
        results = vms.search_similar(query, top_k=3, min_similarity=0.5)
        for r in results:
            print(f"  [{r['similarity']}] {r['content'][:60]}...")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成")
    print(f"📊 总记忆数: {len(vms.memories)}")


if __name__ == "__main__":
    test_vector_search()
