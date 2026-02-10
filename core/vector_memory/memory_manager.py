"""
记忆管理模块

提供记忆导入、增量更新、过期清理和索引优化功能。
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Union

import numpy as np
from tqdm import tqdm

from .embedder import Embedder, EmbeddingConfig
from .memory_search import MemorySearch, SearchConfig, SearchResult
from .vector_store import VectorStore, VectorRecord

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    
    # 数据库配置
    db_path: Path = field(default_factory=lambda: Path("./memory_db"))
    table_name: str = "memories"
    embedding_dim: int = 1024
    
    # 模型配置
    model_name: str = "BAAI/bge-large-zh-v1.5"
    device: str = "auto"
    
    # 导入配置
    memory_files_dir: Optional[Path] = None
    auto_import_on_start: bool = True
    
    # 更新检测配置
    use_content_hash: bool = True
    track_file_changes: bool = True
    
    # 清理配置
    enable_auto_cleanup: bool = True
    max_memory_age_days: int = 365
    cleanup_interval_days: int = 7
    
    # 性能配置
    batch_size: int = 32
    optimize_interval: int = 1000


class MemoryManager:
    """
    记忆管理器
    
    统一管理记忆的导入、存储、搜索和维护。
    
    Attributes:
        config: 配置对象
        vector_store: 向量存储实例
        embedder: 嵌入生成器实例
        searcher: 搜索器实例
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        初始化记忆管理器
        
        Args:
            config: 配置对象
        """
        self.config = config or MemoryConfig()
        
        # 初始化嵌入器
        embed_config = EmbeddingConfig(
            model_name=self.config.model_name,
            device=self.config.device,
            batch_size=self.config.batch_size,
        )
        self.embedder = Embedder(embed_config)
        
        # 初始化向量存储
        self.vector_store = VectorStore(
            db_path=self.config.db_path,
            table_name=self.config.table_name,
            embedding_dim=self.config.embedding_dim,
        )
        self.vector_store.initialize()
        
        # 初始化搜索器
        search_config = SearchConfig()
        self.searcher = MemorySearch(
            vector_store=self.vector_store,
            embedder=self.embedder,
            config=search_config,
        )
        
        # 状态追踪
        self._imported_files: Dict[str, Dict[str, Any]] = {}
        self._stats: Dict[str, int] = {
            "added": 0,
            "updated": 0,
            "deleted": 0,
            "skipped": 0,
        }
        
        # 加载导入状态
        self._load_import_state()
        
        # 自动导入
        if self.config.auto_import_on_start and self.config.memory_files_dir:
            self.import_from_directory(self.config.memory_files_dir)
        
        # 自动清理
        if self.config.enable_auto_cleanup:
            self.cleanup_expired()
    
    def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        record_id: Optional[str] = None,
    ) -> str:
        """
        添加单条记忆
        
        Args:
            content: 记忆内容
            metadata: 元数据
            record_id: 记录ID（自动生成）
            
        Returns:
            记录ID
        """
        # 生成嵌入
        embedding = self.embedder.encode(content)
        if len(embedding.shape) == 2:
            embedding = embedding[0]
        
        # 添加元数据
        meta = metadata or {}
        meta["_content_hash"] = self._compute_hash(content)
        meta["_added_at"] = datetime.now().isoformat()
        
        # 存储
        record_id = self.vector_store.add(
            vector=embedding,
            content=content,
            metadata=meta,
            record_id=record_id,
        )
        
        self._stats["added"] += 1
        
        # 触发优化
        if self._stats["added"] % self.config.optimize_interval == 0:
            self.optimize()
        
        return record_id
    
    def add_memories_batch(
        self,
        contents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        show_progress: bool = False,
    ) -> List[str]:
        """
        批量添加记忆
        
        Args:
            contents: 内容列表
            metadatas: 元数据列表
            show_progress: 是否显示进度
            
        Returns:
            记录ID列表
        """
        if not contents:
            return []
        
        # 批量编码
        embeddings = self.embedder.encode(
            contents,
            show_progress=show_progress,
        )
        
        # 准备记录
        records = []
        for i, (content, embedding) in enumerate(zip(contents, embeddings)):
            meta = (metadatas[i] if metadatas else {}).copy()
            meta["_content_hash"] = self._compute_hash(content)
            meta["_added_at"] = datetime.now().isoformat()
            
            records.append((embedding, content, meta))
        
        # 批量存储
        record_ids = self.vector_store.add_batch(records)
        
        self._stats["added"] += len(record_ids)
        
        return record_ids
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        search_type: str = "hybrid",
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        搜索记忆
        
        Args:
            query: 查询文本
            top_k: 返回结果数
            search_type: 搜索类型 (semantic/keyword/hybrid)
            filter_dict: 过滤条件
            
        Returns:
            搜索结果列表
        """
        if search_type == "semantic":
            return self.searcher.semantic_search(query, top_k, filter_dict)
        elif search_type == "keyword":
            return self.searcher.keyword_search(query, top_k, filter_dict)
        elif search_type == "hybrid":
            return self.searcher.hybrid_search(query, top_k, filter_dict)
        else:
            raise ValueError(f"未知搜索类型: {search_type}")
    
    def update_memory(
        self,
        record_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        更新记忆
        
        Args:
            record_id: 记录ID
            content: 新内容（可选）
            metadata: 新元数据（可选，会合并）
            
        Returns:
            是否更新成功
        """
        new_embedding = None
        if content:
            new_embedding = self.embedder.encode(content)[0]
            if metadata:
                metadata["_content_hash"] = self._compute_hash(content)
                metadata["_updated_at"] = datetime.now().isoformat()
        
        success = self.vector_store.update(
            record_id=record_id,
            vector=new_embedding,
            content=content,
            metadata=metadata,
        )
        
        if success:
            self._stats["updated"] += 1
        
        return success
    
    def delete_memory(self, record_id: str) -> bool:
        """
        删除记忆
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否删除成功
        """
        success = self.vector_store.delete(record_id)
        if success:
            self._stats["deleted"] += 1
        return success
    
    def get_memory(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单条记忆
        
        Args:
            record_id: 记录ID
            
        Returns:
            记忆字典或None
        """
        return self.vector_store.get(record_id)
    
    def import_from_file(
        self,
        file_path: Union[str, Path],
        format: Optional[str] = None,
        auto_chunk: bool = True,
    ) -> int:
        """
        从文件导入记忆
        
        Args:
            file_path: 文件路径
            format: 文件格式 (json/jsonl/md/txt)，自动检测
            auto_chunk: 是否自动分块长文本
            
        Returns:
            导入数量
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return 0
        
        # 检测格式
        format = format or file_path.suffix.lstrip('.')
        
        # 检查是否需要更新
        if self._should_skip_file(file_path):
            logger.info(f"跳过未变更文件: {file_path}")
            self._stats["skipped"] += 1
            return 0
        
        # 解析文件
        contents, metadatas = self._parse_file(file_path, format, auto_chunk)
        
        if not contents:
            return 0
        
        # 批量添加
        record_ids = self.add_memories_batch(
            contents,
            metadatas,
            show_progress=True,
        )
        
        # 更新导入状态
        self._update_import_state(file_path, len(record_ids))
        
        logger.info(f"从 {file_path.name} 导入 {len(record_ids)} 条记忆")
        
        return len(record_ids)
    
    def import_from_directory(
        self,
        directory: Union[str, Path],
        pattern: str = "*.md",
        recursive: bool = True,
    ) -> int:
        """
        从目录导入记忆
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归子目录
            
        Returns:
            导入数量
        """
        directory = Path(directory)
        
        if not directory.exists():
            logger.warning(f"目录不存在: {directory}")
            return 0
        
        # 查找文件
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        logger.info(f"找到 {len(files)} 个文件待导入")
        
        total = 0
        for file_path in tqdm(files, desc="导入文件"):
            count = self.import_from_file(file_path)
            total += count
        
        logger.info(f"目录导入完成，共导入 {total} 条记忆")
        
        return total
    
    def import_from_markdown(
        self,
        content: str,
        source: Optional[str] = None,
        split_by_heading: bool = True,
    ) -> List[str]:
        """
        从Markdown内容导入记忆
        
        Args:
            content: Markdown内容
            source: 来源标识
            split_by_heading: 是否按标题分块
            
        Returns:
            记录ID列表
        """
        if split_by_heading:
            # 按标题分块
            import re
            
            # 匹配Markdown标题
            pattern = r'(^|\n)(#{1,6}\s+.+?)(?=\n#{1,6}\s|\Z)'
            sections = re.split(pattern, content, flags=re.DOTALL)
            
            contents = []
            metadatas = []
            
            current_heading = ""
            for i, section in enumerate(sections):
                if not section.strip():
                    continue
                    
                if section.startswith('#'):
                    current_heading = section.strip()
                else:
                    full_content = f"{current_heading}\n{section}" if current_heading else section
                    contents.append(full_content.strip())
                    metadatas.append({
                        "source": source or "markdown_import",
                        "section": i,
                    })
        else:
            # 自动分块
            contents = self.embedder.chunk_text(content)
            metadatas = [{"source": source or "markdown_import"} for _ in contents]
        
        return self.add_memories_batch(contents, metadatas)
    
    def cleanup_expired(self, max_age_days: Optional[int] = None) -> int:
        """
        清理过期记忆
        
        Args:
            max_age_days: 最大保留天数（覆盖配置）
            
        Returns:
            清理数量
        """
        max_age = max_age_days or self.config.max_memory_age_days
        cutoff_date = datetime.now() - timedelta(days=max_age)
        
        all_records = self.vector_store.get_all()
        
        to_delete = []
        for record in all_records:
            created_at = record.get("created_at")
            if created_at and isinstance(created_at, str):
                try:
                    record_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if record_date < cutoff_date:
                        to_delete.append(record["id"])
                except:
                    pass
        
        # 执行删除
        deleted_count = 0
        for record_id in to_delete:
            if self.vector_store.delete(record_id):
                deleted_count += 1
        
        logger.info(f"清理过期记忆: {deleted_count}/{len(to_delete)}")
        
        # 保存状态
        self._save_import_state()
        
        return deleted_count
    
    def cleanup_duplicates(self, similarity_threshold: float = 0.95) -> int:
        """
        清理重复记忆
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            清理数量
        """
        all_records = self.vector_store.get_all()
        
        if len(all_records) < 2:
            return 0
        
        # 提取向量
        vectors = np.array([r["vector"] for r in all_records])
        
        # 计算相似度矩阵
        from .embedder import Embedder
        
        # 归一化
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors_norm = vectors / (norms + 1e-8)
        
        # 计算相似度
        similarity_matrix = np.dot(vectors_norm, vectors_norm.T)
        
        # 找出重复（上三角矩阵）
        to_delete = set()
        for i in range(len(all_records)):
            for j in range(i + 1, len(all_records)):
                if similarity_matrix[i, j] > similarity_threshold:
                    # 删除较旧的
                    id_i = all_records[i]["id"]
                    id_j = all_records[j]["id"]
                    
                    time_i = all_records[i].get("created_at", "")
                    time_j = all_records[j].get("created_at", "")
                    
                    if time_i < time_j:
                        to_delete.add(id_i)
                    else:
                        to_delete.add(id_j)
        
        # 执行删除
        deleted_count = 0
        for record_id in to_delete:
            if self.vector_store.delete(record_id):
                deleted_count += 1
        
        logger.info(f"清理重复记忆: {deleted_count}/{len(to_delete)}")
        
        return deleted_count
    
    def optimize(self) -> None:
        """优化索引和存储"""
        self.vector_store.optimize()
        self._save_import_state()
        logger.info("索引优化完成")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "total_memories": self.vector_store.count(),
            "added": self._stats["added"],
            "updated": self._stats["updated"],
            "deleted": self._stats["deleted"],
            "skipped": self._stats["skipped"],
            "db_path": str(self.config.db_path),
            "model": self.config.model_name,
        }
    
    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """检查文件是否需要跳过"""
        if not self.config.track_file_changes:
            return False
        
        file_key = str(file_path.resolve())
        
        if file_key not in self._imported_files:
            return False
        
        # 检查修改时间
        current_mtime = file_path.stat().st_mtime
        last_mtime = self._imported_files[file_key].get("mtime", 0)
        
        return current_mtime <= last_mtime
    
    def _update_import_state(self, file_path: Path, count: int) -> None:
        """更新导入状态"""
        file_key = str(file_path.resolve())
        self._imported_files[file_key] = {
            "mtime": file_path.stat().st_mtime,
            "imported_at": datetime.now().isoformat(),
            "count": count,
        }
        self._save_import_state()
    
    def _parse_file(
        self,
        file_path: Path,
        format: str,
        auto_chunk: bool,
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """解析文件内容"""
        content = file_path.read_text(encoding='utf-8')
        
        contents = []
        metadatas = []
        
        base_meta = {
            "source_file": str(file_path),
            "imported_at": datetime.now().isoformat(),
        }
        
        if format in ('json', 'jsonl'):
            # JSON格式
            if format == 'jsonl':
                for line in content.strip().split('\n'):
                    try:
                        data = json.loads(line)
                        text = data.get('content', data.get('text', str(data)))
                        meta = {**base_meta, **data.get('metadata', {})}
                        contents.append(text)
                        metadatas.append(meta)
                    except:
                        pass
            else:
                data = json.loads(content)
                if isinstance(data, list):
                    for item in data:
                        text = item.get('content', item.get('text', str(item)))
                        meta = {**base_meta, **item.get('metadata', {})}
                        contents.append(text)
                        metadatas.append(meta)
        
        elif format in ('md', 'markdown', 'txt'):
            # Markdown/文本格式
            if auto_chunk and len(content) > self.embedder.config.chunk_size:
                # 自动分块
                chunks = self.embedder.chunk_text(content)
                for i, chunk in enumerate(chunks):
                    contents.append(chunk)
                    metadatas.append({
                        **base_meta,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    })
            else:
                contents.append(content)
                metadatas.append(base_meta)
        
        else:
            # 默认作为纯文本处理
            contents.append(content)
            metadatas.append(base_meta)
        
        return contents, metadatas
    
    def _load_import_state(self) -> None:
        """加载导入状态"""
        state_file = self.config.db_path / ".import_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    self._imported_files = json.load(f)
            except Exception as e:
                logger.warning(f"加载导入状态失败: {e}")
                self._imported_files = {}
    
    def _save_import_state(self) -> None:
        """保存导入状态"""
        state_file = self.config.db_path / ".import_state.json"
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(self._imported_files, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存导入状态失败: {e}")
    
    def close(self) -> None:
        """关闭并清理资源"""
        self._save_import_state()
        self.vector_store.close()
        logger.info("记忆管理器已关闭")
    
    def __enter__(self) -> "MemoryManager":
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.close()
