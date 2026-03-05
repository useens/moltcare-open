#!/usr/bin/env python3
"""
统一知识内化系统 - 知识处理与向量化模块

功能：
- 从 raw/ 读取原始情报
- 清洗和结构化处理
- 生成知识摘要
- 存入 processed/
- 关键信息编码到向量数据库

使用现有的向量记忆系统接口
"""

import os
import sys
import json
import re
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector_memory import MemoryManager, MemoryConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class KnowledgeItem:
    """知识条目数据结构"""
    id: str
    title: str
    content: str
    source: str
    source_type: str  # hackernews, github_trending, devto, etc.
    url: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    processed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "source_type": self.source_type,
            "url": self.url,
            "author": self.author,
            "tags": self.tags,
            "summary": self.summary,
            "created_at": self.created_at,
            "processed_at": self.processed_at,
            "raw_data": self.raw_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeItem":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            source=data.get("source", ""),
            source_type=data.get("source_type", ""),
            url=data.get("url"),
            author=data.get("author"),
            tags=data.get("tags", []),
            summary=data.get("summary"),
            raw_data=data.get("raw_data", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            processed_at=data.get("processed_at"),
        )


class KnowledgeCleaner:
    """知识清洗器"""
    
    # 需要过滤的噪声词汇
    NOISE_PATTERNS = [
        r'\[more\]',
        r'\d+\s*points?',
        r'\d+\s*comments?',
        r'^\s*•\s*',
        r'\s+',
    ]
    
    # HTML标签
    HTML_TAGS = re.compile(r'<[^>]+>')
    
    # URL模式
    URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    
    @classmethod
    def clean_text(cls, text: str) -> str:
        """清洗文本"""
        if not text:
            return ""
        
        # 移除HTML标签
        text = cls.HTML_TAGS.sub(' ', text)
        
        # 规范化空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除噪声模式
        for pattern in cls.NOISE_PATTERNS:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # 清理首尾空白
        text = text.strip()
        
        return text
    
    @classmethod
    def extract_urls(cls, text: str) -> List[str]:
        """提取URL"""
        return cls.URL_PATTERN.findall(text)
    
    @classmethod
    def generate_summary(cls, title: str, content: str, max_length: int = 200) -> str:
        """生成知识摘要"""
        # 优先使用标题
        summary_parts = [title]
        
        # 添加内容的前几句
        if content:
            # 按句子分割
            sentences = re.split(r'(?<=[。！？.!?])\s+', content)
            current_length = len(title)
            
            for sentence in sentences:
                if current_length + len(sentence) > max_length:
                    break
                summary_parts.append(sentence.strip())
                current_length += len(sentence)
        
        summary = ' '.join(summary_parts)
        
        # 截断到最大长度
        if len(summary) > max_length:
            summary = summary[:max_length-3] + '...'
        
        return summary


class KnowledgeProcessor:
    """知识处理器"""
    
    def __init__(self, 
                 raw_dir: Path = None,
                 processed_dir: Path = None,
                 db_path: Path = None):
        """
        初始化知识处理器
        
        Args:
            raw_dir: 原始情报目录
            processed_dir: 处理后知识目录
            db_path: 向量数据库路径
        """
        # 设置默认路径 - knowledge_processor.py 在工作区根目录
        base_dir = Path(__file__).parent
        self.raw_dir = raw_dir or base_dir / "memory" / "knowledge" / "raw"
        self.processed_dir = processed_dir or base_dir / "memory" / "knowledge" / "processed"
        self.db_path = db_path or base_dir / "memory" / "knowledge" / "vector_db"
        
        # 确保目录存在
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化向量记忆系统
        config = MemoryConfig(
            db_path=self.db_path,
            table_name="knowledge_vectors",
            embedding_dim=1024,
            model_name="BAAI/bge-large-zh-v1.5",
            batch_size=16,
        )
        self.memory_manager = MemoryManager(config)
        
        # 处理统计
        self.stats = {
            "total_processed": 0,
            "success": 0,
            "failed": 0,
            "vectorized": 0,
        }
    
    def discover_raw_files(self) -> List[Path]:
        """发现原始情报文件"""
        files = []
        
        # 支持的文件格式
        patterns = ['*.json', '*.jsonl', '*.md', '*.txt']
        
        # 在 raw/ 目录递归查找
        for pattern in patterns:
            found = list(self.raw_dir.rglob(pattern))
            files.extend(found)
            if found:
                logger.debug(f"在 raw/ 找到 {len(found)} 个 {pattern} 文件")
        
        # 也去 data/ 目录查找
        data_dir = Path(__file__).parent.parent / "data"
        if data_dir.exists():
            for pattern in patterns:
                found = list(data_dir.rglob(pattern))
                files.extend(found)
                if found:
                    logger.debug(f"在 data/ 找到 {len(found)} 个 {pattern} 文件")
        
        # 过滤掉 cookies.json 和无关文件
        filtered_files = []
        for f in files:
            fname = f.name.lower()
            if 'cookie' not in fname and 'test' not in fname and 'report' not in fname:
                filtered_files.append(f)
        
        # 按修改时间排序
        filtered_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        logger.info(f"发现 {len(filtered_files)} 个原始情报文件 (过滤后)")
        return filtered_files
    
    def parse_raw_file(self, file_path: Path) -> List[KnowledgeItem]:
        """解析原始情报文件"""
        items = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            suffix = file_path.suffix.lower()
            
            # 从文件路径推断源类型
            source_type = self._infer_source_type(file_path)
            
            if suffix in ['.json', '.jsonl']:
                items = self._parse_json_content(content, file_path, source_type)
            elif suffix in ['.md', '.txt']:
                items = self._parse_text_content(content, file_path, source_type)
            
            logger.info(f"从 {file_path.name} 解析出 {len(items)} 条知识")
            
        except Exception as e:
            logger.error(f"解析文件失败 {file_path}: {e}")
        
        return items
    
    def _infer_source_type(self, file_path: Path) -> str:
        """从文件路径推断源类型"""
        path_str = str(file_path).lower()
        
        if 'hackernews' in path_str:
            return 'hackernews'
        elif 'github' in path_str:
            return 'github_trending'
        elif 'devto' in path_str:
            return 'devto'
        elif 'indiehackers' in path_str:
            return 'indiehackers'
        elif 'producthunt' in path_str:
            return 'producthunt'
        elif 'lobsters' in path_str:
            return 'lobsters'
        elif 'browser' in path_str or 'exploration' in path_str:
            return 'browser_exploration'
        else:
            return 'unknown'
    
    def _parse_json_content(self, content: str, file_path: Path, source_type: str) -> List[KnowledgeItem]:
        """解析JSON内容"""
        items = []
        
        try:
            data = json.loads(content)
            
            # 处理列表格式
            if isinstance(data, list):
                for item in data:
                    knowledge = self._convert_to_knowledge(item, source_type, file_path)
                    if knowledge:
                        items.append(knowledge)
            
            # 处理字典格式（可能是单个条目或包含条目的字典）
            elif isinstance(data, dict):
                # 检查是否有列表字段
                for key in ['items', 'stories', 'posts', 'results', 'data']:
                    if key in data and isinstance(data[key], list):
                        for item in data[key]:
                            knowledge = self._convert_to_knowledge(item, source_type, file_path)
                            if knowledge:
                                items.append(knowledge)
                        break
                else:
                    # 单个条目
                    knowledge = self._convert_to_knowledge(data, source_type, file_path)
                    if knowledge:
                        items.append(knowledge)
        
        except json.JSONDecodeError:
            # 尝试按行解析JSONL格式
            for line in content.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    knowledge = self._convert_to_knowledge(item, source_type, file_path)
                    if knowledge:
                        items.append(knowledge)
                except:
                    pass
        
        return items
    
    def _parse_text_content(self, content: str, file_path: Path, source_type: str) -> List[KnowledgeItem]:
        """解析文本/Markdown内容"""
        items = []
        
        # 尝试按标题分割
        sections = re.split(r'\n#{1,3}\s+', content)
        
        if len(sections) > 1:
            for section in sections[1:]:  # 跳过第一个空部分
                lines = section.strip().split('\n', 1)
                title = lines[0].strip() if lines else "Untitled"
                body = lines[1].strip() if len(lines) > 1 else ""
                
                knowledge = KnowledgeItem(
                    id=self._generate_id(title),
                    title=title,
                    content=body,
                    source=str(file_path),
                    source_type=source_type,
                    raw_data={"file": str(file_path)},
                )
                items.append(knowledge)
        else:
            # 整体作为一个条目
            knowledge = KnowledgeItem(
                id=self._generate_id(content[:50]),
                title=file_path.stem,
                content=content,
                source=str(file_path),
                source_type=source_type,
                raw_data={"file": str(file_path)},
            )
            items.append(knowledge)
        
        return items
    
    def _convert_to_knowledge(self, data: Dict[str, Any], source_type: str, file_path: Path) -> Optional[KnowledgeItem]:
        """将原始数据转换为知识条目"""
        try:
            # 提取标题
            title = data.get('title', '') or data.get('name', '') or data.get('headline', 'Untitled')
            title = KnowledgeCleaner.clean_text(title)
            
            # 提取内容
            content = data.get('content', '') or data.get('description', '') or data.get('summary', '')
            content = KnowledgeCleaner.clean_text(content)
            
            # 提取URL
            url = data.get('url', '') or data.get('link', '') or data.get('href', '')
            
            # 提取作者
            author = data.get('author', '') or data.get('user', '') or data.get('by', '')
            
            # 提取标签
            tags = data.get('tags', []) or data.get('categories', [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]
            
            # 生成ID
            item_id = self._generate_id(f"{title}{url}{source_type}")
            
            return KnowledgeItem(
                id=item_id,
                title=title,
                content=content,
                source=str(file_path),
                source_type=source_type,
                url=url if url else None,
                author=author if author else None,
                tags=tags,
                raw_data=data,
            )
        
        except Exception as e:
            logger.warning(f"转换知识条目失败: {e}")
            return None
    
    def _generate_id(self, content: str) -> str:
        """生成唯一ID"""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def process_item(self, item: KnowledgeItem) -> KnowledgeItem:
        """处理单个知识条目"""
        # 清洗标题和内容
        item.title = KnowledgeCleaner.clean_text(item.title)
        item.content = KnowledgeCleaner.clean_text(item.content)
        
        # 生成摘要
        item.summary = KnowledgeCleaner.generate_summary(item.title, item.content)
        
        # 标记处理时间
        item.processed_at = datetime.now().isoformat()
        
        return item
    
    def save_processed_item(self, item: KnowledgeItem) -> Path:
        """保存处理后的知识条目"""
        # 按日期组织目录
        date_dir = self.processed_dir / datetime.now().strftime("%Y%m")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件名
        safe_title = re.sub(r'[^\w\s-]', '', item.title)[:50]
        filename = f"{item.source_type}_{item.id}_{safe_title}.json"
        file_path = date_dir / filename
        
        # 保存为JSON
        file_path.write_text(
            json.dumps(item.to_dict(), ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        return file_path
    
    def vectorize_item(self, item: KnowledgeItem) -> bool:
        """将知识条目编码到向量数据库"""
        try:
            # 构建存储内容
            storage_content = f"{item.title}\n\n{item.content}"
            if item.summary:
                storage_content = f"{item.summary}\n\n{storage_content}"
            
            # 构建元数据
            metadata = {
                "knowledge_id": item.id,
                "title": item.title,
                "source_type": item.source_type,
                "source": item.source,
                "url": item.url,
                "author": item.author,
                "tags": json.dumps(item.tags),
                "summary": item.summary,
                "processed_at": item.processed_at,
            }
            
            # 添加到向量记忆系统
            record_id = self.memory_manager.add_memory(
                content=storage_content,
                metadata=metadata,
                record_id=item.id,
            )
            
            logger.debug(f"向量化成功: {record_id}")
            return True
            
        except Exception as e:
            logger.error(f"向量化失败 {item.id}: {e}")
            return False
    
    def process_all(self) -> Dict[str, int]:
        """
        处理所有原始情报
        
        Returns:
            处理统计信息
        """
        logger.info("=" * 60)
        logger.info("开始知识处理流程")
        logger.info("=" * 60)
        
        # 发现文件
        raw_files = self.discover_raw_files()
        logger.info(f"发现 {len(raw_files)} 个原始情报文件")
        
        if not raw_files:
            logger.info("没有找到原始情报文件")
            return self.stats
        
        # 处理每个文件
        all_items: List[KnowledgeItem] = []
        for file_path in raw_files:
            items = self.parse_raw_file(file_path)
            all_items.extend(items)
        
        logger.info(f"共解析出 {len(all_items)} 条原始知识")
        
        # 去重（基于ID）
        seen_ids = set()
        unique_items = []
        for item in all_items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                unique_items.append(item)
        
        logger.info(f"去重后剩余 {len(unique_items)} 条知识")
        
        # 处理每条知识
        for i, item in enumerate(unique_items, 1):
            try:
                logger.info(f"[{i}/{len(unique_items)}] 处理: {item.title[:50]}...")
                
                # 处理
                processed_item = self.process_item(item)
                
                # 保存
                saved_path = self.save_processed_item(processed_item)
                logger.debug(f"保存到: {saved_path}")
                
                # 向量化
                if self.vectorize_item(processed_item):
                    self.stats["vectorized"] += 1
                
                self.stats["success"] += 1
                
            except Exception as e:
                logger.error(f"处理条目失败: {e}")
                self.stats["failed"] += 1
            
            self.stats["total_processed"] += 1
        
        # 优化索引
        logger.info("优化向量索引...")
        self.memory_manager.optimize()
        
        # 报告统计
        logger.info("=" * 60)
        logger.info("知识处理完成")
        logger.info(f"  总处理数: {self.stats['total_processed']}")
        logger.info(f"  成功: {self.stats['success']}")
        logger.info(f"  失败: {self.stats['failed']}")
        logger.info(f"  向量化: {self.stats['vectorized']}")
        logger.info("=" * 60)
        
        return self.stats
    
    def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索知识库"""
        results = self.memory_manager.search(query, top_k=top_k, search_type="hybrid")
        return [
            {
                "id": r.id,
                "score": r.score,
                "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                "metadata": r.metadata,
            }
            for r in results
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        memory_stats = self.memory_manager.get_stats()
        return {
            **self.stats,
            **memory_stats,
            "raw_dir": str(self.raw_dir),
            "processed_dir": str(self.processed_dir),
            "db_path": str(self.db_path),
        }
    
    def close(self):
        """关闭资源"""
        if hasattr(self, 'memory_manager'):
            self.memory_manager.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """主函数"""
    # 创建处理器实例
    with KnowledgeProcessor() as processor:
        # 调试输出
        logger.info(f"raw_dir: {processor.raw_dir}")
        logger.info(f"raw_dir exists: {processor.raw_dir.exists()}")
        
        # 执行处理
        stats = processor.process_all()
        
        # 打印结果
        print("\n" + "=" * 60)
        print("知识处理报告")
        print("=" * 60)
        print(f"处理的知识条目数: {stats['total_processed']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failed']}")
        print(f"向量化: {stats['vectorized']}")
        print("=" * 60)
    
    return stats


if __name__ == "__main__":
    main()
