"""
记忆搜索模块

提供语义搜索、混合搜索和结果排序功能。
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from .embedder import Embedder
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果数据类"""
    
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    created_at: Optional[str] = None
    
    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"SearchResult(id={self.id}, score={self.score:.4f}, content='{content_preview}')"


@dataclass  
class SearchConfig:
    """搜索配置"""
    
    # 语义搜索权重
    semantic_weight: float = 0.7
    # 关键词搜索权重
    keyword_weight: float = 0.3
    # 结果阈值（低于此值的会被过滤）
    score_threshold: float = 0.0
    # 时间衰减因子（越大越优先考虑新内容）
    time_decay_factor: float = 0.0
    # 最大结果数
    max_results: int = 10
    # 是否使用重排序
    use_rerank: bool = False
    # 重排序模型
    rerank_model: Optional[str] = None


class MemorySearch:
    """
    记忆搜索器
    
    提供语义搜索、关键词搜索和混合搜索功能。
    
    Attributes:
        vector_store: 向量存储实例
        embedder: 嵌入生成器实例
        config: 搜索配置
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Embedder,
        config: Optional[SearchConfig] = None,
    ):
        """
        初始化搜索器
        
        Args:
            vector_store: 向量存储实例
            embedder: 嵌入生成器实例
            config: 搜索配置
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.config = config or SearchConfig()
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        语义搜索
        
        基于向量相似度搜索相关记忆。
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 元数据过滤条件
            
        Returns:
            搜索结果列表
        """
        # 生成查询向量
        query_embedding = self.embedder.encode(query)
        if len(query_embedding.shape) == 2:
            query_embedding = query_embedding[0]
        
        # 构建过滤表达式
        filter_expr = self._build_filter_expression(filter_dict)
        
        # 向量搜索
        results = self.vector_store.search(
            query_vector=query_embedding,
            top_k=top_k * 2,  # 多获取一些用于后处理
            filter_expr=filter_expr,
        )
        
        # 转换为SearchResult
        search_results = []
        for r in results:
            # LanceDB返回的是距离，需要转换为相似度
            distance = r.get("_distance", 0)
            # Cosine distance to similarity
            similarity = 1.0 - distance
            
            result = SearchResult(
                id=r["id"],
                content=r["content"],
                score=similarity,
                metadata=r.get("metadata", {}),
                semantic_score=similarity,
                created_at=str(r.get("created_at", "")),
            )
            search_results.append(result)
        
        # 应用阈值过滤
        search_results = [
            r for r in search_results 
            if r.semantic_score >= self.config.score_threshold
        ]
        
        # 应用时间衰减
        if self.config.time_decay_factor > 0:
            search_results = self._apply_time_decay(search_results)
        
        # 重排序
        if self.config.use_rerank:
            search_results = self._rerank_results(query, search_results)
        
        return search_results[:top_k]
    
    def keyword_search(
        self,
        query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        关键词搜索
        
        基于关键词匹配搜索相关记忆。
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 元数据过滤条件
            
        Returns:
            搜索结果列表
        """
        # 提取查询关键词
        query_keywords = self._extract_keywords(query)
        
        # 获取候选记录（这里从向量存储获取所有，实际应用可考虑使用倒排索引）
        filter_expr = self._build_filter_expression(filter_dict)
        
        # 简化处理：从store获取数据并本地过滤
        all_records = self.vector_store.get_all()
        
        scored_results = []
        for record in all_records:
            content = record["content"]
            score = self._compute_keyword_score(query_keywords, content)
            
            if score > 0:
                result = SearchResult(
                    id=record["id"],
                    content=content,
                    score=score,
                    metadata=record.get("metadata", {}),
                    keyword_score=score,
                    created_at=str(record.get("created_at", "")),
                )
                scored_results.append(result)
        
        # 按分数排序
        scored_results.sort(key=lambda x: x.score, reverse=True)
        
        # 应用阈值
        scored_results = [
            r for r in scored_results 
            if r.score >= self.config.score_threshold
        ]
        
        return scored_results[:top_k]
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        semantic_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        混合搜索
        
        结合语义搜索和关键词搜索的结果。
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 元数据过滤条件
            semantic_weight: 语义搜索权重（覆盖配置）
            keyword_weight: 关键词搜索权重（覆盖配置）
            
        Returns:
            搜索结果列表
        """
        sem_weight = semantic_weight or self.config.semantic_weight
        key_weight = keyword_weight or self.config.keyword_weight
        
        # 归一化权重
        total_weight = sem_weight + key_weight
        sem_weight /= total_weight
        key_weight /= total_weight
        
        # 并行执行两种搜索
        semantic_results = self.semantic_search(
            query, top_k=top_k * 2, filter_dict=filter_dict
        )
        keyword_results = self.keyword_search(
            query, top_k=top_k * 2, filter_dict=filter_dict
        )
        
        # 合并结果
        merged = self._merge_results(
            semantic_results, 
            keyword_results,
            sem_weight,
            key_weight,
        )
        
        # 应用时间衰减
        if self.config.time_decay_factor > 0:
            merged = self._apply_time_decay(merged)
        
        # 重排序
        if self.config.use_rerank:
            merged = self._rerank_results(query, merged)
        
        return merged[:top_k]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取：分词并过滤
        # 支持中英文
        import re
        
        # 提取中文词汇
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', text)
        # 提取英文单词
        english_words = re.findall(r'[a-zA-Z]+', text)
        
        keywords = []
        
        # 中文：按字符作为关键词（简化处理）
        for word in chinese_words:
            # 过滤短词
            if len(word) >= 2:
                keywords.append(word)
        
        # 英文：转小写
        for word in english_words:
            word_lower = word.lower()
            if len(word_lower) >= 2:
                keywords.append(word_lower)
        
        return list(set(keywords))  # 去重
    
    def _compute_keyword_score(self, keywords: List[str], content: str) -> float:
        """计算关键词匹配分数"""
        if not keywords:
            return 0.0
        
        content_lower = content.lower()
        score = 0.0
        
        for keyword in keywords:
            # 精确匹配
            if keyword in content_lower:
                # 根据词频计算
                count = content_lower.count(keyword)
                # 长关键词权重更高
                weight = min(len(keyword) / 5.0, 2.0)
                score += count * weight
        
        # 归一化
        max_possible = len(keywords) * 2.0
        return min(score / max_possible, 1.0) if max_possible > 0 else 0.0
    
    def _merge_results(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        sem_weight: float,
        key_weight: float,
    ) -> List[SearchResult]:
        """合并语义和关键词搜索结果"""
        # 构建ID到结果的映射
        merged_dict: Dict[str, SearchResult] = {}
        
        # 处理语义结果
        for r in semantic_results:
            r.score = r.semantic_score * sem_weight
            merged_dict[r.id] = r
        
        # 处理关键词结果
        for r in keyword_results:
            if r.id in merged_dict:
                # 已存在，合并分数
                existing = merged_dict[r.id]
                existing.keyword_score = r.keyword_score
                existing.score += r.keyword_score * key_weight
            else:
                # 新结果
                r.score = r.keyword_score * key_weight
                merged_dict[r.id] = r
        
        # 转换为列表并排序
        results = list(merged_dict.values())
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _build_filter_expression(self, filter_dict: Optional[Dict[str, Any]]) -> Optional[str]:
        """构建过滤表达式"""
        if not filter_dict:
            return None
        
        conditions = []
        for key, value in filter_dict.items():
            if isinstance(value, str):
                # 字符串匹配（contains）
                # 注意：LanceDB的metadata存储为JSON字符串，这里简化处理
                conditions.append(f"metadata LIKE '%{key}%{value}%'")
            elif isinstance(value, (int, float)):
                conditions.append(f"metadata LIKE '%{key}%{value}%'")
            elif isinstance(value, bool):
                conditions.append(f"metadata LIKE '%{key}%{str(value).lower()}%'")
        
        return " AND ".join(conditions) if conditions else None
    
    def _apply_time_decay(self, results: List[SearchResult]) -> List[SearchResult]:
        """应用时间衰减因子"""
        from datetime import datetime
        
        now = datetime.now()
        
        for r in results:
            try:
                if r.created_at:
                    created = datetime.fromisoformat(r.created_at.replace('Z', '+00:00'))
                    # 计算时间差（天）
                    days_old = (now - created).days
                    # 衰减公式：新内容分数更高
                    decay = np.exp(-self.config.time_decay_factor * days_old / 30)
                    r.score *= decay
            except:
                pass
        
        # 重新排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _rerank_results(
        self,
        query: str,
        results: List[SearchResult],
    ) -> List[SearchResult]:
        """
        重排序结果
        
        使用更精确的模型进行重排序。
        """
        if not results or not self.config.rerank_model:
            return results
        
        try:
            # 这里可以集成ColBERT等重排序模型
            # 简化实现：使用embedder计算更精确的相似度
            query_emb = self.embedder.encode(query)[0]
            
            for r in results:
                content_emb = self.embedder.encode(r.content)[0]
                # 重新计算余弦相似度
                similarity = np.dot(query_emb, content_emb) / (
                    np.linalg.norm(query_emb) * np.linalg.norm(content_emb) + 1e-8
                )
                # 融合原始分数和新分数
                r.score = 0.5 * r.score + 0.5 * similarity
            
            results.sort(key=lambda x: x.score, reverse=True)
            
        except Exception as e:
            logger.warning(f"重排序失败: {e}")
        
        return results
    
    def search_by_vector(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        通过向量直接搜索
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_dict: 元数据过滤条件
            
        Returns:
            搜索结果列表
        """
        filter_expr = self._build_filter_expression(filter_dict)
        
        results = self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            filter_expr=filter_expr,
        )
        
        search_results = []
        for r in results:
            distance = r.get("_distance", 0)
            similarity = 1.0 - distance
            
            result = SearchResult(
                id=r["id"],
                content=r["content"],
                score=similarity,
                metadata=r.get("metadata", {}),
                semantic_score=similarity,
            )
            search_results.append(result)
        
        return search_results
    
    def add_filter(
        self,
        key: str,
        value: Any,
    ) -> "MemorySearch":
        """
        添加默认过滤条件（链式调用）
        
        Args:
            key: 过滤键
            value: 过滤值
            
        Returns:
            self
        """
        if not hasattr(self, '_default_filters'):
            self._default_filters = {}
        self._default_filters[key] = value
        return self
