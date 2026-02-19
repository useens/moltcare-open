"""
文本嵌入生成模块

提供文本分块、嵌入生成和批量处理功能。
支持中英文文本和多模型切换。
"""

import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterator, List, Optional, Union, Callable

import numpy as np
from tqdm import tqdm

logger = logging.getLogger(__name__)

# 导入共享模型池
try:
    from core.shared_models import get_model
    USE_SHARED_POOL = True
except ImportError:
    get_model = None
    USE_SHARED_POOL = False
    logger.warning("无法导入共享模型池，将使用独立模型实例")


@dataclass
class EmbeddingConfig:
    """嵌入模型配置"""
    
    model_name: str = "BAAI/bge-large-zh-v1.5"
    device: str = "auto"  # auto, cpu, cuda
    normalize_embeddings: bool = True
    batch_size: int = 32
    max_seq_length: int = 512
    trust_remote_code: bool = True
    
    # 分块配置
    chunk_size: int = 512
    chunk_overlap: int = 50
    chunk_by: str = "token"  # token, sentence, paragraph


class TextChunker:
    """
    智能文本分块器
    
    支持按token、句子或段落进行分块，保留语义完整性。
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunk_by: str = "token",
    ):
        """
        初始化分块器
        
        Args:
            chunk_size: 每块的最大token数/字符数
            chunk_overlap: 块之间的重叠大小
            chunk_by: 分块方式 (token/sentence/paragraph)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunk_by = chunk_by
        
        # 句子分隔符（中英文兼容）
        self.sentence_delimiters = r'(?<=[。！？.!?])\s*'
        self.paragraph_delimiters = r'\n\s*\n'
    
    def split(self, text: str) -> List[str]:
        """
        分割文本为块
        
        Args:
            text: 输入文本
            
        Returns:
            文本块列表
        """
        if not text or not text.strip():
            return []
        
        if self.chunk_by == "token":
            return self._split_by_token(text)
        elif self.chunk_by == "sentence":
            return self._split_by_sentence(text)
        elif self.chunk_by == "paragraph":
            return self._split_by_paragraph(text)
        else:
            raise ValueError(f"未知的分块方式: {self.chunk_by}")
    
    def _split_by_token(self, text: str) -> List[str]:
        """按近似token数量分块（按字符估算）"""
        # 简单估算：中文1字符≈1token，英文按空格分割
        # 更精确的估算需要tokenizer，这里使用保守估计
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        # 按字符分割，但尽量保留完整词汇
        words = re.findall(r'\S+', text)
        
        for word in words:
            word_size = len(word)  # 中文字符数或英文单词长度
            
            if current_size + word_size > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                # 保留重叠部分
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap // 4)
                current_chunk = current_chunk[overlap_start:] + [word]
                current_size = sum(len(w) for w in current_chunk)
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _split_by_sentence(self, text: str) -> List[str]:
        """按句子分块"""
        sentences = re.split(self.sentence_delimiters, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                # 保留重叠的句子
                overlap_size = 0
                overlap_sentences = []
                for s in reversed(current_chunk):
                    if overlap_size + len(s) < self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += len(s)
                    else:
                        break
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _split_by_paragraph(self, text: str) -> List[str]:
        """按段落分块"""
        paragraphs = re.split(self.paragraph_delimiters, text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > self.chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks
    
    def split_iter(self, text: str) -> Iterator[str]:
        """迭代器方式分块"""
        yield from self.split(text)


class Embedder:
    """
    文本嵌入生成器
    
    支持多模型懒加载、批量嵌入和缓存机制。
    
    Attributes:
        config: 配置对象
        model: 加载的SentenceTransformer模型
        _model_cache: 模型缓存字典
    """
    
    # 类级别的模型缓存
    _model_cache: dict = {}
    _cache_lock = False
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        初始化嵌入器
        
        Args:
            config: 配置对象，默认使用默认配置
        """
        self.config = config or EmbeddingConfig()
        self._model = None
        self._chunker = TextChunker(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            chunk_by=self.config.chunk_by,
        )
    
    @property
    def model(self):
        """懒加载模型"""
        if self._model is None:
            self._model = self._load_model()
        return self._model
    
    def _load_model(self):
        """
        加载嵌入模型（使用共享模型池）

        Returns:
            SentenceTransformer模型实例
        """
        model_name = self.config.model_name

        # 优先使用共享模型池
        if USE_SHARED_POOL:
            logger.info(f"从共享模型池加载: {model_name}")
            return get_model(
                model_name,
                device=self.config.device if self.config.device != "auto" else None,
                trust_remote_code=self.config.trust_remote_code,
            )

        # 回退到原有缓存机制
        cache_key = f"{model_name}_{self.config.device}"

        # 检查缓存
        if cache_key in self._model_cache:
            logger.info(f"使用类级缓存模型: {model_name}")
            return self._model_cache[cache_key]

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"正在加载模型: {model_name}")

            # 确定设备
            device = self.config.device
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"

            model = SentenceTransformer(
                model_name,
                device=device,
                trust_remote_code=self.config.trust_remote_code,
            )

            # 设置最大序列长度
            if hasattr(model, "max_seq_length"):
                model.max_seq_length = self.config.max_seq_length

            # 存入缓存
            self._model_cache[cache_key] = model
            logger.info(f"模型加载完成，使用设备: {device}")

            return model

        except ImportError:
            raise ImportError(
                "sentence-transformers未安装，请运行: "
                "pip install sentence-transformers>=3.0.0"
            )
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        编码文本为向量
        
        Args:
            texts: 单个文本或文本列表
            show_progress: 是否显示进度条
            
        Returns:
            嵌入向量数组 (N, embedding_dim)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=self.config.normalize_embeddings,
            convert_to_numpy=True,
        )
        
        return embeddings
    
    def encode_with_chunks(
        self,
        text: str,
        aggregate: str = "mean",
    ) -> np.ndarray:
        """
        编码长文本（自动分块并聚合）
        
        Args:
            text: 输入文本
            aggregate: 聚合方式 (mean/sum/max/first)
            
        Returns:
            聚合后的嵌入向量
        """
        chunks = self._chunker.split(text)
        
        if not chunks:
            # 空文本返回零向量
            return np.zeros(self.get_dimension())
        
        if len(chunks) == 1:
            return self.encode(chunks[0])[0]
        
        # 编码所有块
        embeddings = self.encode(chunks)
        
        # 聚合
        if aggregate == "mean":
            return np.mean(embeddings, axis=0)
        elif aggregate == "sum":
            return np.sum(embeddings, axis=0)
        elif aggregate == "max":
            return np.max(embeddings, axis=0)
        elif aggregate == "first":
            return embeddings[0]
        else:
            raise ValueError(f"未知的聚合方式: {aggregate}")
    
    def encode_batch(
        self,
        texts: List[str],
        chunk_long_texts: bool = False,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        批量编码
        
        Args:
            texts: 文本列表
            chunk_long_texts: 是否对长文本自动分块
            show_progress: 是否显示进度条
            
        Returns:
            嵌入向量数组
        """
        if not texts:
            return np.array([])
        
        if not chunk_long_texts:
            return self.encode(texts, show_progress=show_progress)
        
        # 长文本分块处理
        all_embeddings = []
        text_iter = tqdm(texts, desc="Encoding") if show_progress else texts
        
        for text in text_iter:
            embedding = self.encode_with_chunks(text)
            all_embeddings.append(embedding)
        
        return np.array(all_embeddings)
    
    def get_dimension(self) -> int:
        """
        获取嵌入维度
        
        Returns:
            向量维度
        """
        return self.model.get_sentence_embedding_dimension()
    
    def chunk_text(self, text: str) -> List[str]:
        """
        分块文本
        
        Args:
            text: 输入文本
            
        Returns:
            文本块列表
        """
        return self._chunker.split(text)
    
    def compute_similarity(
        self,
        embeddings1: np.ndarray,
        embeddings2: np.ndarray,
    ) -> np.ndarray:
        """
        计算向量间余弦相似度
        
        Args:
            embeddings1: 第一组向量 (N, D)
            embeddings2: 第二组向量 (M, D)
            
        Returns:
            相似度矩阵 (N, M)
        """
        # 归一化
        norm1 = np.linalg.norm(embeddings1, axis=1, keepdims=True)
        norm2 = np.linalg.norm(embeddings2, axis=1, keepdims=True)
        
        embeddings1_norm = embeddings1 / (norm1 + 1e-8)
        embeddings2_norm = embeddings2 / (norm2 + 1e-8)
        
        # 计算余弦相似度
        similarity = np.dot(embeddings1_norm, embeddings2_norm.T)
        
        return similarity
    
    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        corpus_embeddings: np.ndarray,
        top_k: int = 5,
    ) -> List[tuple]:
        """
        查找最相似的向量
        
        Args:
            query_embedding: 查询向量 (D,)
            corpus_embeddings: 语料库向量 (N, D)
            top_k: 返回前k个
            
        Returns:
            [(index, score), ...] 列表
        """
        similarities = self.compute_similarity(
            query_embedding.reshape(1, -1),
            corpus_embeddings,
        )[0]
        
        # 获取top_k索引
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [(int(idx), float(similarities[idx])) for idx in top_indices]
    
    @classmethod
    def clear_cache(cls) -> None:
        """清除模型缓存"""
        cls._model_cache.clear()
        logger.info("模型缓存已清除")
    
    @classmethod
    def get_cached_models(cls) -> List[str]:
        """获取缓存中的模型列表"""
        return list(cls._model_cache.keys())
