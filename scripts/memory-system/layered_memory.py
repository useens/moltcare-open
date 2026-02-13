#!/usr/bin/env python3
"""
记忆系统重构 v5.1 - 核心架构
分层记忆 + 自动整理 + 向量检索 + 关联图谱
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import sys

# 路径配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DIR = MEMORY_DIR / "vector"
ARCHIVE_DIR = MEMORY_DIR / "archive"
ASSOC_DIR = MEMORY_DIR / "associations"
TEMP_DIR = MEMORY_DIR / "temp"
DAILY_DIR = MEMORY_DIR / "daily"

# 确保目录存在
for d in [VECTOR_DIR, ARCHIVE_DIR, ASSOC_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class MemoryEntry:
    """记忆条目 - 统一格式"""
    
    def __init__(self, content: str, source: str, memory_type: str, 
                 importance: int = 5, tags: List[str] = None):
        self.id = hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        self.content = content
        self.source = source  # 来源: daily/2026-02-11.md, conversation, evolution等
        self.type = memory_type  # 类型: decision, insight, error, learning, user_pref
        self.importance = importance  # 1-10重要性
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
        self.access_count = 0
        self.last_accessed = self.created_at
        
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "type": self.type,
            "importance": self.importance,
            "tags": self.tags,
            "created_at": self.created_at,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryEntry':
        entry = cls(
            content=data["content"],
            source=data["source"],
            memory_type=data["type"],
            importance=data.get("importance", 5),
            tags=data.get("tags", [])
        )
        entry.id = data["id"]
        entry.created_at = data["created_at"]
        entry.access_count = data.get("access_count", 0)
        entry.last_accessed = data.get("last_accessed", entry.created_at)
        return entry


class LayeredMemorySystem:
    """分层记忆系统 - v5.1核心"""
    
    def __init__(self):
        self.working_memory: List[MemoryEntry] = []  # 工作记忆（当前会话）
        self.short_term_file = TEMP_DIR / "short_term.json"
        self.long_term_file = VECTOR_DIR / "long_term_memories.json"
        self.assoc_file = ASSOC_DIR / "memory_graph.json"
        
    # ========== 工作记忆（短期）==========
    
    def add_to_working_memory(self, entry: MemoryEntry):
        """添加到工作记忆（限制容量，防止溢出）"""
        self.working_memory.append(entry)
        # 工作记忆最多保留50条，超过时归档到短期
        if len(self.working_memory) > 50:
            oldest = self.working_memory.pop(0)
            self._archive_to_short_term(oldest)
    
    def get_working_memory(self, query: str = None, limit: int = 10) -> List[MemoryEntry]:
        """获取工作记忆，支持简单过滤"""
        if query:
            return [m for m in self.working_memory if query.lower() in m.content.lower()][-limit:]
        return self.working_memory[-limit:]
    
    # ========== 短期记忆 ==========
    
    def _archive_to_short_term(self, entry: MemoryEntry):
        """归档到短期记忆"""
        memories = self._load_short_term()
        memories.append(entry.to_dict())
        # 短期记忆最多保留200条
        if len(memories) > 200:
            # 按重要性排序，保留重要的
            memories.sort(key=lambda x: x["importance"], reverse=True)
            removed = memories[200:]
            memories = memories[:200]
            # 被移除的归档到长期
            for r in removed:
                if r["importance"] >= 7:
                    self._archive_to_long_term(MemoryEntry.from_dict(r))
        
        with open(self.short_term_file, 'w', encoding='utf-8') as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
    
    def _load_short_term(self) -> List[Dict]:
        """加载短期记忆"""
        if self.short_term_file.exists():
            with open(self.short_term_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    # ========== 长期记忆（向量）==========
    
    def _archive_to_long_term(self, entry: MemoryEntry):
        """归档到长期记忆（向量化）"""
        # 这里将集成向量记忆系统
        # 简化版：先存储到JSON，后续导入向量DB
        memories = self._load_long_term()
        memories.append(entry.to_dict())
        
        with open(self.long_term_file, 'w', encoding='utf-8') as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
    
    def _load_long_term(self) -> List[Dict]:
        """加载长期记忆"""
        if self.long_term_file.exists():
            with open(self.long_term_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def search_long_term(self, query: str, min_importance: int = 5) -> List[MemoryEntry]:
        """搜索长期记忆（简化版关键词搜索，后续改为向量检索）"""
        memories = self._load_long_term()
        results = []
        query_lower = query.lower()
        
        for m in memories:
            if m["importance"] >= min_importance:
                # 简单的关键词匹配（后续改为语义相似度）
                score = 0
                if query_lower in m["content"].lower():
                    score += 10
                # 标签匹配
                for tag in m.get("tags", []):
                    if query_lower in tag.lower():
                        score += 5
                
                if score > 0:
                    entry = MemoryEntry.from_dict(m)
                    entry.access_count += 1
                    entry.last_accessed = datetime.now().isoformat()
                    results.append((score, entry))
        
        # 按分数排序
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:10]]
    
    # ========== 记忆关联 ==========
    
    def add_association(self, memory_id1: str, memory_id2: str, relation: str):
        """添加记忆关联"""
        graph = self._load_association_graph()
        
        if memory_id1 not in graph:
            graph[memory_id1] = []
        
        # 避免重复
        existing = [a for a in graph[memory_id1] if a["to"] == memory_id2]
        if not existing:
            graph[memory_id1].append({
                "to": memory_id2,
                "relation": relation,
                "created_at": datetime.now().isoformat()
            })
        
        with open(self.assoc_file, 'w', encoding='utf-8') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
    
    def _load_association_graph(self) -> Dict:
        """加载关联图谱"""
        if self.assoc_file.exists():
            with open(self.assoc_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_related_memories(self, memory_id: str) -> List[str]:
        """获取关联的记忆ID"""
        graph = self._load_association_graph()
        return [a["to"] for a in graph.get(memory_id, [])]
    
    # ========== 记忆整理（自动归档）==========
    
    def consolidate_daily_memories(self, date_str: str = None):
        """整理每日记忆 - 从daily文件提取重要内容"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        daily_file = DAILY_DIR / f"{date_str}.md"
        if not daily_file.exists():
            return 0
        
        with open(daily_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取重要决策和洞察
        extracted = self._extract_important_items(content, daily_file.name)
        
        # 归档到长期记忆
        for item in extracted:
            self._archive_to_long_term(item)
        
        return len(extracted)
    
    def _extract_important_items(self, content: str, source: str) -> List[MemoryEntry]:
        """从内容中提取重要项目"""
        entries = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # 检测重要标记
            if line.startswith('# ') or line.startswith('## '):
                # 章节标题
                entries.append(MemoryEntry(
                    content=line.lstrip('# ').strip(),
                    source=source,
                    memory_type="topic",
                    importance=6,
                    tags=["header"]
                ))
            elif '✅' in line or '❌' in line or '⚠️' in line:
                # 决策/结果标记
                entries.append(MemoryEntry(
                    content=line,
                    source=source,
                    memory_type="decision",
                    importance=8,
                    tags=["decision", "result"]
                ))
            elif 'zxl' in line.lower() or '用户' in line:
                # 用户指令
                entries.append(MemoryEntry(
                    content=line,
                    source=source,
                    memory_type="user_pref",
                    importance=9,
                    tags=["user", "instruction"]
                ))
        
        return entries
    
    # ========== 记忆检索（上下文感知）==========
    
    def context_aware_retrieval(self, context: str, max_results: int = 5) -> List[MemoryEntry]:
        """上下文感知记忆检索"""
        results = []
        
        # 1. 从工作记忆检索
        working = self.get_working_memory(context, limit=3)
        results.extend(working)
        
        # 2. 从长期记忆检索
        long_term = self.search_long_term(context)
        results.extend(long_term)
        
        # 3. 去重并排序
        seen_ids = set()
        unique_results = []
        for r in results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique_results.append(r)
        
        # 按重要性排序
        unique_results.sort(key=lambda x: x.importance, reverse=True)
        return unique_results[:max_results]


# 单例模式
_memory_system = None

def get_memory_system() -> LayeredMemorySystem:
    """获取记忆系统单例"""
    global _memory_system
    if _memory_system is None:
        _memory_system = LayeredMemorySystem()
    return _memory_system


if __name__ == "__main__":
    # 测试
    ms = get_memory_system()
    
    # 添加测试记忆
    entry = MemoryEntry(
        content="测试记忆：v5.1记忆系统重构完成",
        source="test",
        memory_type="milestone",
        importance=10,
        tags=["v5.1", "memory_system"]
    )
    ms.add_to_working_memory(entry)
    
    # 整理今日记忆
    count = ms.consolidate_daily_memories("2026-02-11")
    print(f"整理了 {count} 条记忆")
    
    # 检索测试
    results = ms.context_aware_retrieval("记忆系统")
    print(f"检索到 {len(results)} 条相关记忆")
    for r in results:
        print(f"  - [{r.type}] {r.content[:50]}...")
