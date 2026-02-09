#!/usr/bin/env python3
"""
Memory Indexer - 向量记忆索引器

功能：
1. 扫描 memory/modules/ 下的所有 .md 文件
2. 提取文本并进行分块处理
3. 使用 sentence-transformers 生成向量
4. 本地存储（NumPy + JSON）
5. 支持增量更新

用法：
    python indexer.py              # 完整重建索引
    python indexer.py --incremental # 增量更新
    python indexer.py --stats       # 显示统计信息
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

import numpy as np

# 尝试导入 sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("错误: 需要安装 sentence-transformers")
    print("运行: pip install sentence-transformers")
    sys.exit(1)


class Config:
    """配置类"""
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DIM = 384  # all-MiniLM-L6-v2 的输出维度
    CHUNK_SIZE = 512  # 每个文本块的最大字符数
    CHUNK_OVERLAP = 128  # 块之间的重叠字符数
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.modules_dir = self.base_dir.parent / "modules"
        
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
        
        # 文件路径
        self.vectors_file = self.data_dir / "vectors.npy"
        self.metadata_file = self.data_dir / "metadata.json"
        self.index_file = self.data_dir / "index.json"
        self.config_file = self.data_dir / "config.json"
    
    def save(self):
        """保存配置"""
        config = {
            "model": self.DEFAULT_MODEL,
            "vector_dim": self.VECTOR_DIM,
            "chunk_size": self.CHUNK_SIZE,
            "chunk_overlap": self.CHUNK_OVERLAP,
            "updated_at": datetime.now().isoformat()
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def load(self) -> Dict:
        """加载配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}


class TextChunker:
    """文本分块器"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 128):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        将文本分块，使用滑动窗口策略
        
        Args:
            text: 输入文本
            
        Returns:
            文本块列表
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 尝试在句子边界处分割
            if end < len(text):
                # 查找最近的句子结束符
                for sep in ['。', '；', '\n\n', '. ', '; ', '\n']:
                    pos = text.rfind(sep, start, end)
                    if pos != -1:
                        end = pos + len(sep)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 滑动窗口
            start = end - self.chunk_overlap
            
            # 防止无限循环
            if start >= end:
                start = end
        
        return chunks


class MemoryIndexer:
    """记忆索引器主类"""
    
    def __init__(
        self,
        modules_dir: str = None,
        model_name: str = None,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.config = Config()
        
        # 使用传入参数或默认值
        self.modules_dir = Path(modules_dir) if modules_dir else self.config.modules_dir
        self.model_name = model_name or Config.DEFAULT_MODEL
        self.chunk_size = chunk_size or Config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP
        
        # 初始化组件
        self.chunker = TextChunker(self.chunk_size, self.chunk_overlap)
        self.model = None  # 延迟加载
        
        # 内存中的索引数据
        self.vectors: Optional[np.ndarray] = None
        self.metadata: List[Dict] = []
        self.file_hashes: Dict[str, str] = {}  # 文件路径 -> MD5哈希
        
        # 加载现有索引
        self._load_existing_index()
    
    def _load_model(self):
        """延迟加载模型"""
        if self.model is None:
            print(f"正在加载模型: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print("模型加载完成")
    
    def _load_existing_index(self):
        """加载现有索引"""
        # 加载向量
        if self.config.vectors_file.exists():
            self.vectors = np.load(self.config.vectors_file)
            print(f"已加载 {len(self.vectors)} 个向量")
        
        # 加载元数据
        if self.config.metadata_file.exists():
            with open(self.config.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metadata = data.get('chunks', [])
                self.file_hashes = data.get('file_hashes', {})
            print(f"已加载 {len(self.metadata)} 个元数据记录")
    
    def _compute_file_hash(self, filepath: Path) -> str:
        """计算文件MD5哈希"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _extract_metadata(self, content: str, filepath: Path) -> Dict:
        """从Markdown内容提取元数据"""
        metadata = {
            'title': '',
            'tags': [],
            'links': []
        }
        
        lines = content.split('\n')
        
        # 提取标题（第一个#开头的行）
        for line in lines:
            if line.startswith('# '):
                metadata['title'] = line[2:].strip()
                break
            elif line.startswith('## ') and not metadata['title']:
                metadata['title'] = line[3:].strip()
        
        if not metadata['title']:
            metadata['title'] = filepath.stem
        
        # 提取标签（#标签 格式）
        import re
        tags = re.findall(r'#([^#\s][^\s]*)', content)
        metadata['tags'] = list(set(tags))  # 去重
        
        # 提取Wiki链接 [[...]]
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        metadata['links'] = links
        
        return metadata
    
    def _get_md_files(self) -> List[Path]:
        """获取所有Markdown文件"""
        if not self.modules_dir.exists():
            print(f"警告: 目录不存在 {self.modules_dir}")
            return []
        
        md_files = list(self.modules_dir.rglob("*.md"))
        print(f"找到 {len(md_files)} 个Markdown文件")
        return md_files
    
    def _process_file(self, filepath: Path) -> List[Dict]:
        """处理单个文件，返回块列表"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  错误: 无法读取 {filepath}: {e}")
            return []
        
        # 提取元数据
        doc_metadata = self._extract_metadata(content, filepath)
        
        # 分块
        chunks = self.chunker.chunk_text(content)
        
        # 生成块记录
        chunk_records = []
        for i, chunk_text in enumerate(chunks):
            record = {
                'id': f"{filepath.stem}_{i}",
                'file_path': str(filepath.relative_to(self.modules_dir.parent)),
                'file_name': filepath.name,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'title': doc_metadata['title'],
                'tags': doc_metadata['tags'],
                'links': doc_metadata['links'],
                'text': chunk_text,
                'char_count': len(chunk_text),
                'indexed_at': datetime.now().isoformat()
            }
            chunk_records.append(record)
        
        return chunk_records
    
    def _encode_chunks(self, chunks: List[Dict]) -> np.ndarray:
        """将文本块编码为向量"""
        self._load_model()
        
        texts = [chunk['text'] for chunk in chunks]
        print(f"  正在编码 {len(texts)} 个文本块...")
        
        # 批量编码
        vectors = self.model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # 归一化，便于余弦相似度计算
        )
        
        return vectors.astype(np.float32)
    
    def build_index(self, force: bool = False):
        """
        完整重建索引
        
        Args:
            force: 强制重建，即使索引已存在
        """
        if not force and self.vectors is not None and len(self.vectors) > 0:
            print(f"索引已存在 ({len(self.vectors)} 向量)，使用 --force 重建")
            return
        
        print("=" * 50)
        print("开始构建向量索引")
        print("=" * 50)
        
        # 收集所有文件
        md_files = self._get_md_files()
        if not md_files:
            print("没有找到Markdown文件")
            return
        
        # 处理所有文件
        all_chunks = []
        new_file_hashes = {}
        
        for i, filepath in enumerate(md_files, 1):
            print(f"[{i}/{len(md_files)}] 处理: {filepath.name}")
            
            chunks = self._process_file(filepath)
            if chunks:
                all_chunks.extend(chunks)
                new_file_hashes[str(filepath)] = self._compute_file_hash(filepath)
        
        if not all_chunks:
            print("没有提取到任何文本块")
            return
        
        print(f"\n总共 {len(all_chunks)} 个文本块")
        
        # 编码向量化
        print("\n开始向量化...")
        vectors = self._encode_chunks(all_chunks)
        
        # 保存索引
        self._save_index(vectors, all_chunks, new_file_hashes)
        
        print("\n✅ 索引构建完成!")
        self._print_stats(vectors, all_chunks)
    
    def incremental_update(self):
        """增量更新索引"""
        print("=" * 50)
        print("开始增量更新")
        print("=" * 50)
        
        md_files = self._get_md_files()
        if not md_files:
            return
        
        # 检测变更
        changed_files = []
        new_files = []
        removed_files = set(self.file_hashes.keys())
        
        for filepath in md_files:
            path_str = str(filepath)
            current_hash = self._compute_file_hash(filepath)
            
            if path_str in self.file_hashes:
                removed_files.discard(path_str)
                if self.file_hashes[path_str] != current_hash:
                    changed_files.append(filepath)
            else:
                new_files.append(filepath)
            
            self.file_hashes[path_str] = current_hash
        
        print(f"新增: {len(new_files)}, 修改: {len(changed_files)}, 删除: {len(removed_files)}")
        
        if not new_files and not changed_files and not removed_files:
            print("没有变更，跳过更新")
            return
        
        # 收集需要处理的文件
        files_to_process = new_files + changed_files
        
        if removed_files:
            # 删除已移除文件的向量
            self._remove_files_from_index(removed_files)
        
        if files_to_process:
            # 处理新增/修改的文件
            new_chunks = []
            for filepath in files_to_process:
                print(f"处理: {filepath.name}")
                chunks = self._process_file(filepath)
                new_chunks.extend(chunks)
            
            if new_chunks:
                # 编码新向量
                new_vectors = self._encode_chunks(new_chunks)
                
                # 合并向量
                if self.vectors is not None and len(self.vectors) > 0:
                    self.vectors = np.vstack([self.vectors, new_vectors])
                else:
                    self.vectors = new_vectors
                
                # 合并元数据
                self.metadata.extend(new_chunks)
        
        # 保存索引
        self._save_index(self.vectors, self.metadata, self.file_hashes)
        
        print("\n✅ 增量更新完成!")
        self._print_stats(self.vectors, self.metadata)
    
    def _remove_files_from_index(self, file_paths: set):
        """从索引中移除指定文件的向量"""
        if not self.metadata or self.vectors is None:
            return
        
        # 找到要删除的索引
        indices_to_remove = []
        for i, meta in enumerate(self.metadata):
            full_path = str(self.modules_dir.parent / meta['file_path'])
            if full_path in file_paths:
                indices_to_remove.append(i)
        
        if not indices_to_remove:
            return
        
        print(f"  移除 {len(indices_to_remove)} 个旧向量")
        
        # 删除向量（从后向前删除，避免索引变化）
        mask = np.ones(len(self.metadata), dtype=bool)
        mask[indices_to_remove] = False
        
        self.vectors = self.vectors[mask]
        self.metadata = [m for i, m in enumerate(self.metadata) if mask[i]]
    
    def _save_index(self, vectors: np.ndarray, metadata: List[Dict], file_hashes: Dict):
        """保存索引到磁盘"""
        # 保存向量
        np.save(self.config.vectors_file, vectors)
        
        # 保存元数据
        data = {
            'chunks': metadata,
            'file_hashes': file_hashes,
            'updated_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        with open(self.config.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 保存配置
        self.config.save()
        
        print(f"\n索引已保存到: {self.config.data_dir}")
    
    def _print_stats(self, vectors: np.ndarray, metadata: List[Dict]):
        """打印统计信息"""
        print("\n" + "=" * 50)
        print("索引统计")
        print("=" * 50)
        print(f"向量数量: {len(vectors)}")
        print(f"向量维度: {vectors.shape[1]}")
        print(f"唯一文件: {len(set(m['file_path'] for m in metadata))}")
        print(f"存储大小: {self._get_storage_size()}")
    
    def _get_storage_size(self) -> str:
        """获取索引存储大小"""
        total_size = 0
        for file in self.config.data_dir.iterdir():
            if file.is_file():
                total_size += file.stat().st_size
        
        if total_size < 1024:
            return f"{total_size} B"
        elif total_size < 1024 * 1024:
            return f"{total_size / 1024:.2f} KB"
        else:
            return f"{total_size / (1024 * 1024):.2f} MB"
    
    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        if self.vectors is None:
            return {"error": "索引不存在"}
        
        files = set(m['file_path'] for m in self.metadata)
        all_tags = []
        for m in self.metadata:
            all_tags.extend(m.get('tags', []))
        
        return {
            "vector_count": len(self.vectors),
            "vector_dim": self.vectors.shape[1],
            "unique_files": len(files),
            "total_chunks": len(self.metadata),
            "unique_tags": len(set(all_tags)),
            "storage_size": self._get_storage_size(),
            "model": self.model_name
        }


def main():
    parser = argparse.ArgumentParser(description='向量记忆索引器')
    parser.add_argument('--incremental', '-i', action='store_true', help='增量更新')
    parser.add_argument('--stats', '-s', action='store_true', help='显示统计信息')
    parser.add_argument('--force', '-f', action='store_true', help='强制重建索引')
    parser.add_argument('--modules-dir', '-m', type=str, help='指定模块目录')
    
    args = parser.parse_args()
    
    # 创建索引器
    indexer = MemoryIndexer(modules_dir=args.modules_dir)
    
    if args.stats:
        stats = indexer.get_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    elif args.incremental:
        indexer.incremental_update()
    else:
        indexer.build_index(force=args.force)


if __name__ == "__main__":
    main()
