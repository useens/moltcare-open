# 语义记忆检索系统 - RSI 实验 #3
"""
配置本地 embedding 模型，实现真正的语义召回
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib

class SemanticMemory:
    """语义记忆检索系统"""
    
    def __init__(self, memory_dir: str = "/root/.openclaw/workspace/memory"):
        self.memory_dir = Path(memory_dir)
        self.embedding_cache_dir = Path("/root/.openclaw/workspace/data/embeddings")
        self.embedding_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置本地 embedding（使用轻量级模型）
        self.embedding_config = {
            'provider': 'local',  # 可选: local, openai, voyage
            'model': 'BAAI/bge-small-en-v1.5',  # 轻量级模型，适合本地运行
            'dimension': 384,
            'batch_size': 32,
        }
        
        # 检查是否可用
        self._check_embedding_available()
    
    def _check_embedding_available(self) -> bool:
        """检查 embedding 服务是否可用"""
        try:
            # 尝试导入 sentence-transformers
            import importlib
            spec = importlib.util.find_spec("sentence_transformers")
            if spec is None:
                self.embedding_config['available'] = False
                self.embedding_config['fallback'] = 'fts'
                return False
            
            self.embedding_config['available'] = True
            return True
        except Exception:
            self.embedding_config['available'] = False
            self.embedding_config['fallback'] = 'fts'
            return False
    
    def _get_file_hash(self, content: str) -> str:
        """获取内容哈希，用于缓存"""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _load_or_compute_embedding(self, text: str) -> Optional[List[float]]:
        """加载缓存的 embedding 或计算新的"""
        if not self.embedding_config['available']:
            return None
        
        text_hash = self._get_file_hash(text)
        cache_file = self.embedding_cache_dir / f"{text_hash}.json"
        
        # 检查缓存
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # 计算新的 embedding
        try:
            from sentence_transformers import SentenceTransformer
            
            # 懒加载模型
            if not hasattr(self, '_model'):
                print(f"🔄 加载 embedding 模型: {self.embedding_config['model']}")
                self._model = SentenceTransformer(self.embedding_config['model'])
            
            embedding = self._model.encode(text).tolist()
            
            # 缓存
            with open(cache_file, 'w') as f:
                json.dump(embedding, f)
            
            return embedding
        except Exception as e:
            print(f"⚠️  Embedding 计算失败: {e}")
            return None
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        语义搜索记忆
        
        流程:
        1. 如果 embedding 可用，用向量相似度搜索
        2. 否则 fallback 到 FTS
        """
        query_embedding = self._load_or_compute_embedding(query)
        
        if query_embedding and self.embedding_config['available']:
            return self._semantic_search(query_embedding, top_k)
        else:
            return self._fts_fallback(query, top_k)
    
    def _semantic_search(self, query_embedding: List[float], top_k: int) -> List[Dict]:
        """基于向量相似度的搜索"""
        import numpy as np
        
        results = []
        
        # 遍历记忆文件
        for memory_file in self.memory_dir.glob("**/*.md"):
            try:
                content = memory_file.read_text()
                
                # 分段处理（简单分段）
                segments = self._segment_content(content)
                
                for segment in segments:
                    seg_embedding = self._load_or_compute_embedding(segment)
                    if seg_embedding:
                        # 计算余弦相似度
                        similarity = self._cosine_similarity(
                            query_embedding, seg_embedding
                        )
                        results.append({
                            'file': str(memory_file),
                            'content': segment[:500],
                            'score': similarity,
                            'type': 'semantic'
                        })
            except Exception as e:
                print(f"⚠️  处理文件失败 {memory_file}: {e}")
        
        # 排序并返回 top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _fts_fallback(self, query: str, top_k: int) -> List[Dict]:
        """FTS 回退搜索"""
        from memory_search import memory_search
        
        results = memory_search(query, maxResults=top_k)
        return [
            {
                'file': r.get('path', 'unknown'),
                'content': r.get('content', '')[:500],
                'score': r.get('score', 0),
                'type': 'fts'
            }
            for r in results.get('results', [])
        ]
    
    def _segment_content(self, content: str, max_length: int = 500) -> List[str]:
        """将长内容分段"""
        segments = []
        lines = content.split('\n')
        current_segment = []
        current_length = 0
        
        for line in lines:
            if current_length + len(line) > max_length:
                if current_segment:
                    segments.append('\n'.join(current_segment))
                current_segment = [line]
                current_length = len(line)
            else:
                current_segment.append(line)
                current_length += len(line)
        
        if current_segment:
            segments.append('\n'.join(current_segment))
        
        return segments
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            'embedding_available': self.embedding_config['available'],
            'model': self.embedding_config['model'],
            'fallback': self.embedding_config['fallback'],
            'cache_files': len(list(self.embedding_cache_dir.glob('*.json'))),
        }

# 全局实例
semantic_memory = SemanticMemory()
