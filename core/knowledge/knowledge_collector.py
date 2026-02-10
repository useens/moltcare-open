"""
知识收集器 (Knowledge Collector)
负责从各种来源收集原始知识数据
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict


@dataclass
class RawKnowledge:
    """原始知识数据结构"""
    id: str
    source: str  # 来源：web, chat, file, etc.
    content: str
    metadata: Dict[str, Any]
    timestamp: float
    tags: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RawKnowledge':
        return cls(**data)


class KnowledgeCollector:
    """
    知识收集器
    
    职责：
    1. 接收来自不同来源的原始知识
    2. 标准化数据格式
    3. 存储到 raw 目录
    4. 提供查询和检索接口
    """
    
    def __init__(self, base_path: str = "memory/knowledge"):
        self.base_path = Path(base_path)
        self.raw_path = self.base_path / "raw"
        self._ensure_directories()
        
    def _ensure_directories(self):
        """确保目录结构存在"""
        self.raw_path.mkdir(parents=True, exist_ok=True)
        
    def collect(self, 
                content: str, 
                source: str, 
                metadata: Optional[Dict] = None,
                tags: Optional[List[str]] = None) -> RawKnowledge:
        """
        收集一条原始知识
        
        Args:
            content: 知识内容
            source: 来源标识 (web, chat, file, etc.)
            metadata: 附加元数据
            tags: 标签列表
            
        Returns:
            RawKnowledge 对象
        """
        knowledge = RawKnowledge(
            id=self._generate_id(),
            source=source,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.now().timestamp(),
            tags=tags or []
        )
        
        self._save_raw(knowledge)
        return knowledge
    
    def collect_batch(self, items: List[Dict]) -> List[RawKnowledge]:
        """
        批量收集知识
        
        Args:
            items: 包含 content, source, metadata, tags 的字典列表
            
        Returns:
            RawKnowledge 对象列表
        """
        results = []
        for item in items:
            knowledge = self.collect(
                content=item['content'],
                source=item['source'],
                metadata=item.get('metadata', {}),
                tags=item.get('tags', [])
            )
            results.append(knowledge)
        return results
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return f"raw_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
    
    def _save_raw(self, knowledge: RawKnowledge):
        """保存原始知识到文件"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = self.raw_path / f"{date_str}.jsonl"
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(knowledge.to_dict(), ensure_ascii=False) + '\n')
    
    def list_raw(self, date: Optional[str] = None, limit: int = 100) -> List[RawKnowledge]:
        """
        列出原始知识
        
        Args:
            date: 日期过滤 (YYYY-MM-DD)，None 表示所有
            limit: 最大返回数量
            
        Returns:
            RawKnowledge 列表
        """
        results = []
        
        if date:
            files = [self.raw_path / f"{date}.jsonl"]
        else:
            files = sorted(self.raw_path.glob("*.jsonl"), reverse=True)
        
        for file_path in files:
            if not file_path.exists():
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if len(results) >= limit:
                        break
                    data = json.loads(line.strip())
                    results.append(RawKnowledge.from_dict(data))
        
        return results[:limit]
    
    def get_by_id(self, knowledge_id: str) -> Optional[RawKnowledge]:
        """通过ID获取原始知识"""
        for file_path in self.raw_path.glob("*.jsonl"):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    if data['id'] == knowledge_id:
                        return RawKnowledge.from_dict(data)
        return None
    
    def search(self, query: str, limit: int = 20) -> List[RawKnowledge]:
        """
        简单文本搜索（可扩展为向量搜索）
        
        Args:
            query: 搜索关键词
            limit: 最大返回数量
            
        Returns:
            匹配的 RawKnowledge 列表
        """
        results = []
        query_lower = query.lower()
        
        for knowledge in self.list_raw(limit=1000):
            if (query_lower in knowledge.content.lower() or 
                any(query_lower in tag.lower() for tag in knowledge.tags)):
                results.append(knowledge)
                if len(results) >= limit:
                    break
        
        return results
