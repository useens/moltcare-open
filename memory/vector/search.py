#!/usr/bin/env python3
"""
Memory Search - 语义搜索模块

功能：
1. 加载索引数据（向量 + 元数据）
2. 将查询转换为向量
3. 使用余弦相似度进行搜索
4. 返回排序后的结果

用法：
    from search import MemorySearch
    
    search = MemorySearch()
    results = search.query("安全审计", top_k=5)
"""

import os
import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError("需要安装 sentence-transformers: pip install sentence-transformers")


@dataclass
class SearchResult:
    """搜索结果数据类"""
    id: str
    score: float
    title: str
    file_path: str
    file_name: str
    text: str
    tags: List[str]
    chunk_index: int
    total_chunks: int
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'score': round(self.score, 4),
            'title': self.title,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'text': self.text[:200] + '...' if len(self.text) > 200 else self.text,
            'tags': self.tags,
            'chunk_index': self.chunk_index,
            'total_chunks': self.total_chunks
        }


class MemorySearch:
    """记忆搜索类"""
    
    def __init__(self, data_dir: str = None, model_name: str = None):
        """
        初始化搜索器
        
        Args:
            data_dir: 索引数据目录，默认使用同级目录下的data/
            model_name: 使用的模型名称
        """
        # 确定数据目录
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent / "data"
        
        self.vectors_file = self.data_dir / "vectors.npy"
        self.metadata_file = self.data_dir / "metadata.json"
        
        # 模型（延迟加载）
        self.model_name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        self.model = None
        
        # 索引数据
        self.vectors: Optional[np.ndarray] = None
        self.metadata: List[Dict] = []
        
        # 加载索引
        self._load_index()
    
    def _load_model(self):
        """延迟加载模型"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
    
    def _load_index(self):
        """加载索引数据"""
        if not self.vectors_file.exists():
            raise FileNotFoundError(f"索引不存在: {self.vectors_file}\n请先运行 indexer.py 构建索引")
        
        if not self.metadata_file.exists():
            raise FileNotFoundError(f"元数据不存在: {self.metadata_file}")
        
        # 加载向量
        self.vectors = np.load(self.vectors_file)
        
        # 加载元数据
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.metadata = data.get('chunks', [])
        
        print(f"搜索器已加载: {len(self.vectors)} 个向量, {len(self.metadata)} 个元数据")
    
    def _encode_query(self, query: str) -> np.ndarray:
        """将查询编码为向量"""
        self._load_model()
        
        vector = self.model.encode(
            [query],
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        return vector.astype(np.float32)
    
    def _cosine_similarity(self, query_vec: np.ndarray) -> np.ndarray:
        """
        计算余弦相似度
        
        由于向量已归一化，点积等于余弦相似度
        """
        # query_vec: (1, dim), self.vectors: (n, dim)
        # 结果: (n,)
        return np.dot(self.vectors, query_vec.T).flatten()
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        执行语义搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件，如 {"tags": ["安全"], "file_name": "user"}
            min_score: 最小相似度分数 (0-1)
            
        Returns:
            搜索结果列表
        """
        if self.vectors is None or len(self.vectors) == 0:
            return []
        
        # 编码查询
        query_vec = self._encode_query(query)
        
        # 计算相似度
        similarities = self._cosine_similarity(query_vec)
        
        # 获取排序后的索引
        top_indices = np.argsort(similarities)[::-1]
        
        # 构建结果
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            
            # 分数过滤
            if score < min_score:
                continue
            
            meta = self.metadata[idx]
            
            # 应用过滤条件
            if filters:
                skip = False
                for key, value in filters.items():
                    if key == 'tags':
                        # 标签过滤：需要包含所有指定标签
                        meta_tags = set(meta.get('tags', []))
                        if isinstance(value, str):
                            value = [value]
                        if not all(tag in meta_tags for tag in value):
                            skip = True
                            break
                    elif key == 'file_name':
                        if value.lower() not in meta.get('file_name', '').lower():
                            skip = True
                            break
                    elif key == 'file_path':
                        if value.lower() not in meta.get('file_path', '').lower():
                            skip = True
                            break
                
                if skip:
                    continue
            
            result = SearchResult(
                id=meta['id'],
                score=score,
                title=meta.get('title', ''),
                file_path=meta.get('file_path', ''),
                file_name=meta.get('file_name', ''),
                text=meta.get('text', ''),
                tags=meta.get('tags', []),
                chunk_index=meta.get('chunk_index', 0),
                total_chunks=meta.get('total_chunks', 1)
            )
            
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        return results
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        **kwargs
    ) -> List[Dict]:
        """
        简化的搜索接口，返回字典列表
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            **kwargs: 其他参数传递给query()
            
        Returns:
            字典列表，每个字典包含搜索结果
        """
        results = self.query(query, top_k=top_k, **kwargs)
        return [r.to_dict() for r in results]
    
    def get_document(self, file_path: str) -> List[SearchResult]:
        """
        获取指定文档的所有块
        
        Args:
            file_path: 文档路径（相对于memory目录）
            
        Returns:
            该文档的所有块，按chunk_index排序
        """
        results = []
        for i, meta in enumerate(self.metadata):
            if meta.get('file_path') == file_path:
                # 计算相似度（这里用1.0表示完全匹配）
                result = SearchResult(
                    id=meta['id'],
                    score=1.0,
                    title=meta.get('title', ''),
                    file_path=meta.get('file_path', ''),
                    file_name=meta.get('file_name', ''),
                    text=meta.get('text', ''),
                    tags=meta.get('tags', []),
                    chunk_index=meta.get('chunk_index', 0),
                    total_chunks=meta.get('total_chunks', 1)
                )
                results.append(result)
        
        # 按chunk_index排序
        results.sort(key=lambda x: x.chunk_index)
        return results
    
    def get_related(self, file_path: str, top_k: int = 3) -> List[Dict]:
        """
        获取与指定文档相关的其他文档
        
        基于文档标题进行语义搜索
        
        Args:
            file_path: 参考文档路径
            top_k: 返回相关文档数量
            
        Returns:
            相关文档列表
        """
        # 获取文档标题
        doc_chunks = self.get_document(file_path)
        if not doc_chunks:
            return []
        
        title = doc_chunks[0].title
        
        # 用标题搜索，排除自身
        results = self.query(title, top_k=top_k + 5)
        
        # 过滤掉同一文件
        related = []
        for r in results:
            if r.file_path != file_path and len(related) < top_k:
                related.append(r.to_dict())
        
        return related
    
    def get_stats(self) -> Dict:
        """获取搜索器统计信息"""
        return {
            "total_vectors": len(self.vectors) if self.vectors is not None else 0,
            "vector_dim": self.vectors.shape[1] if self.vectors is not None else 0,
            "total_documents": len(set(m['file_path'] for m in self.metadata)),
            "model": self.model_name
        }


def format_results(results: List[SearchResult], show_tags: bool = True) -> str:
    """
    格式化搜索结果用于显示
    
    Args:
        results: 搜索结果列表
        show_tags: 是否显示标签
        
    Returns:
        格式化字符串
    """
    if not results:
        return "没有找到相关结果"
    
    lines = []
    lines.append(f"找到 {len(results)} 个相关结果:\n")
    
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.title}")
        lines.append(f"    相似度: {r.score:.3f} | 文件: {r.file_name}")
        
        if show_tags and r.tags:
            lines.append(f"    标签: {', '.join(r.tags[:5])}")
        
        # 显示文本预览
        preview = r.text[:150].replace('\n', ' ')
        if len(r.text) > 150:
            preview += "..."
        lines.append(f"    {preview}")
        lines.append("")
    
    return "\n".join(lines)


# 命令行接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='语义搜索')
    parser.add_argument('query', type=str, help='搜索查询')
    parser.add_argument('-k', '--top-k', type=int, default=5, help='返回结果数量')
    parser.add_argument('-t', '--tags', type=str, help='标签过滤（逗号分隔）')
    parser.add_argument('-f', '--file', type=str, help='文件名过滤')
    parser.add_argument('--min-score', type=float, default=0.0, help='最小相似度')
    
    args = parser.parse_args()
    
    # 创建搜索器
    search = MemorySearch()
    
    # 构建过滤条件
    filters = {}
    if args.tags:
        filters['tags'] = [t.strip() for t in args.tags.split(',')]
    if args.file:
        filters['file_name'] = args.file
    
    # 执行搜索
    results = search.query(
        args.query,
        top_k=args.top_k,
        filters=filters if filters else None,
        min_score=args.min_score
    )
    
    # 显示结果
    print(format_results(results))
