#!/usr/bin/env python3
"""
Vestige-like FSRS-6 Memory System
基于FSRS-6间隔重复算法的记忆系统实现

FSRS-6核心公式:
- S'(d, s, r) = s * (1 + e^(1.5) * (11 - d) / s^(-0.015) * (e^(3.5r) - 1))
- D'(d, s, r) = d - e^(-1.1s) * (d - 1) * (0.97 + 0.15r)
- R(t, s) = (1 + t/(9*s))^(-1)

参考: https://github.com/open-spaced-repetition/fsrs4anki/wiki/FSRS-6
"""

import math
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

# FSRS-6 默认参数
DEFAULT_PARAMS = {
    'w1': 0.4072, 'w2': 1.1829, 'w3': 3.1262, 'w4': 15.4722,
    'w5': 7.2102, 'w6': 0.5316, 'w7': 1.0651, 'w8': 0.0239,
    'w9': 1.2500, 'w10': 0.0000, 'w11': 1.6000, 'w12': 2.2500,
    'w13': 0.0100, 'w14': 0.0000, 'w15': 1.0000, 'w16': 0.0000,
    'w17': 3.0000, 'w18': 0.0000, 'w19': 1.0000,
    'request_retention': 0.9,  # 目标保留率
}

@dataclass
class MemoryItem:
    """记忆条目数据结构"""
    id: str
    content: str
    created_at: str
    updated_at: str
    difficulty: float  # 难度 (1-10)
    stability: float   # 稳定性 (天数)
    retrievability: float  # 可提取性 (0-1)
    reps: int          # 重复次数
    lapses: int        # 失败次数
    last_review: Optional[str] = None
    next_review: Optional[str] = None
    tags: List[str] = None
    signal_score: float = 5.0  # Signal评分 (1-10)
    source: str = "manual"
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

def generate_id(content: str) -> str:
    """生成记忆ID"""
    return hashlib.md5(content.encode()).hexdigest()[:16]

def calculate_retrievability(elapsed_days: float, stability: float) -> float:
    """
    计算可提取性 R(t, s)
    R = (1 + t/(9*s))^(-1)
    """
    if stability <= 0:
        return 0.0
    return (1 + elapsed_days / (9 * stability)) ** (-1)

def calculate_next_difficulty(difficulty: float, stability: float, 
                               retrievability: float, rating: int) -> float:
    """
    计算下次难度 D'
    rating: 1=忘记, 2=困难, 3=良好, 4=简单
    """
    # 基于FSRS-6的难度更新公式简化版
    if rating == 1:  # 忘记
        new_diff = min(10, difficulty + 1)
    elif rating == 2:  # 困难
        new_diff = min(10, difficulty + 0.3)
    elif rating == 3:  # 良好
        new_diff = max(1, difficulty - 0.1)
    else:  # 简单
        new_diff = max(1, difficulty - 0.3)
    
    return new_diff

def calculate_next_stability(difficulty: float, stability: float,
                              retrievability: float, rating: int) -> float:
    """
    计算下次稳定性 S'
    基于FSRS-6的核心算法简化
    """
    # 简化版稳定性计算
    if rating == 1:  # 忘记
        new_stab = max(1, stability * 0.5)
    elif rating == 2:  # 困难
        new_stab = stability * 1.1
    elif rating == 3:  # 良好
        new_stab = stability * 1.8
    else:  # 简单
        new_stab = stability * 2.5
    
    # 难度对稳定性的影响
    difficulty_factor = (11 - difficulty) / 10  # 难度越低，因子越大
    new_stab *= (1 + 0.1 * difficulty_factor)
    
    return new_stab

def calculate_interval(stability: float, request_retention: float = 0.9) -> int:
    """
    计算复习间隔
    I = S * ln(R) / ln(0.9)  (近似)
    """
    if stability <= 0:
        return 1
    # 使用对数关系计算间隔
    interval = stability * math.log(request_retention) / math.log(0.9)
    return max(1, int(interval))

def combine_signal_fsrs(signal_score: float, fsrs_priority: float) -> float:
    """
    结合Signal评分和FSRS优先级
    最终优先级 = α * Signal + β * FSRS
    """
    alpha = 0.4  # Signal权重
    beta = 0.6   # FSRS权重
    
    # 归一化到0-10范围
    normalized_fsrs = min(10, fsrs_priority)
    combined = alpha * signal_score + beta * normalized_fsrs
    
    return combined

class VestigeMemory:
    """Vestige-like 记忆管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path.home() / ".local/share/vestige/vestige.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TEXT,
                    updated_at TEXT,
                    difficulty REAL DEFAULT 5.0,
                    stability REAL DEFAULT 1.0,
                    retrievability REAL DEFAULT 1.0,
                    reps INTEGER DEFAULT 0,
                    lapses INTEGER DEFAULT 0,
                    last_review TEXT,
                    next_review TEXT,
                    tags TEXT,
                    signal_score REAL DEFAULT 5.0,
                    source TEXT DEFAULT 'manual'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_next_review 
                ON memories(next_review)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_signal 
                ON memories(signal_score DESC)
            """)
    
    def ingest(self, content: str, tags: List[str] = None, 
               signal_score: float = 5.0, source: str = "manual") -> MemoryItem:
        """添加新记忆"""
        memory_id = generate_id(content)
        now = datetime.now().isoformat()
        
        memory = MemoryItem(
            id=memory_id,
            content=content,
            created_at=now,
            updated_at=now,
            difficulty=5.0,
            stability=1.0,
            retrievability=1.0,
            reps=0,
            lapses=0,
            next_review=now,  # 新记忆立即复习
            tags=tags or [],
            signal_score=signal_score,
            source=source
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memories 
                (id, content, created_at, updated_at, difficulty, stability,
                 retrievability, reps, lapses, next_review, tags, signal_score, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id, memory.content, memory.created_at, memory.updated_at,
                memory.difficulty, memory.stability, memory.retrievability,
                memory.reps, memory.lapses, memory.next_review,
                json.dumps(memory.tags), memory.signal_score, memory.source
            ))
        
        return memory
    
    def review(self, memory_id: str, rating: int) -> Optional[MemoryItem]:
        """
        复习记忆
        rating: 1=忘记, 2=困难, 3=良好, 4=简单
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
            
            if not row:
                return None
            
            # 解析当前状态
            memory = self._row_to_memory(row)
            
            # 计算经过的天数
            if memory.last_review:
                last = datetime.fromisoformat(memory.last_review)
                elapsed = (datetime.now() - last).days
            else:
                elapsed = 0
            
            # 计算当前可提取性
            retrievability = calculate_retrievability(elapsed, memory.stability)
            
            # 更新难度和稳定性
            new_difficulty = calculate_next_difficulty(
                memory.difficulty, memory.stability, retrievability, rating
            )
            new_stability = calculate_next_stability(
                memory.difficulty, memory.stability, retrievability, rating
            )
            
            # 更新统计
            reps = memory.reps + 1
            lapses = memory.lapses + (1 if rating == 1 else 0)
            
            # 计算下次复习时间
            interval = calculate_interval(new_stability)
            next_review = (datetime.now() + timedelta(days=interval)).isoformat()
            
            # 更新数据库
            conn.execute("""
                UPDATE memories SET
                    difficulty = ?, stability = ?, retrievability = ?,
                    reps = ?, lapses = ?, last_review = ?, next_review = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                new_difficulty, new_stability, retrievability,
                reps, lapses, datetime.now().isoformat(), next_review,
                datetime.now().isoformat(), memory_id
            ))
            
            memory.difficulty = new_difficulty
            memory.stability = new_stability
            memory.retrievability = retrievability
            memory.reps = reps
            memory.lapses = lapses
            memory.last_review = datetime.now().isoformat()
            memory.next_review = next_review
            
            return memory
    
    def get_due_memories(self, limit: int = 10) -> List[MemoryItem]:
        """获取到期的记忆"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT * FROM memories 
                WHERE next_review <= ?
                ORDER BY signal_score DESC, next_review ASC
                LIMIT ?
            """, (now, limit)).fetchall()
            
            return [self._row_to_memory(row) for row in rows]
    
    def get_priority_queue(self, limit: int = 20) -> List[Tuple[MemoryItem, float]]:
        """
        获取优先级队列 (Signal + FSRS)
        返回: [(memory, combined_priority), ...]
        """
        memories = self.get_due_memories(limit * 2)
        
        prioritized = []
        for memory in memories:
            # 计算FSRS优先级 (基于可提取性和稳定性)
            elapsed = 0
            if memory.last_review:
                last = datetime.fromisoformat(memory.last_review)
                elapsed = (datetime.now() - last).days
            
            retrievability = calculate_retrievability(elapsed, memory.stability)
            # 可提取性越低，优先级越高
            fsrs_priority = (1 - retrievability) * 10
            
            # 结合Signal和FSRS
            combined = combine_signal_fsrs(memory.signal_score, fsrs_priority)
            prioritized.append((memory, combined))
        
        # 按综合优先级排序
        prioritized.sort(key=lambda x: x[1], reverse=True)
        return prioritized[:limit]
    
    def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """搜索记忆 (简化版关键词搜索)"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT * FROM memories 
                WHERE content LIKE ? OR tags LIKE ?
                ORDER BY signal_score DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit)).fetchall()
            
            return [self._row_to_memory(row) for row in rows]
    
    def promote(self, memory_id: str, delta: float = 1.0):
        """提升记忆重要性"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE memories 
                SET signal_score = min(10, signal_score + ?),
                    updated_at = ?
                WHERE id = ?
            """, (delta, datetime.now().isoformat(), memory_id))
    
    def demote(self, memory_id: str, delta: float = 1.0):
        """降低记忆重要性"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE memories 
                SET signal_score = max(1, signal_score - ?),
                    updated_at = ?
                WHERE id = ?
            """, (delta, datetime.now().isoformat(), memory_id))
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            due = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE next_review <= ?",
                (datetime.now().isoformat(),)
            ).fetchone()[0]
            avg_signal = conn.execute(
                "SELECT AVG(signal_score) FROM memories"
            ).fetchone()[0] or 0
            
            return {
                "total_memories": total,
                "due_for_review": due,
                "average_signal": round(avg_signal, 2),
                "db_path": str(self.db_path)
            }
    
    def _row_to_memory(self, row) -> MemoryItem:
        """数据库行转MemoryItem"""
        return MemoryItem(
            id=row[0],
            content=row[1],
            created_at=row[2],
            updated_at=row[3],
            difficulty=row[4],
            stability=row[5],
            retrievability=row[6],
            reps=row[7],
            lapses=row[8],
            last_review=row[9],
            next_review=row[10],
            tags=json.loads(row[11]) if row[11] else [],
            signal_score=row[12],
            source=row[13]
        )
    
    def export_all(self) -> List[Dict]:
        """导出所有记忆"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM memories").fetchall()
            return [asdict(self._row_to_memory(row)) for row in rows]
    
    def import_memories(self, memories: List[Dict]):
        """导入记忆"""
        for mem_dict in memories:
            memory = MemoryItem(**mem_dict)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memories 
                    (id, content, created_at, updated_at, difficulty, stability,
                     retrievability, reps, lapses, last_review, next_review, 
                     tags, signal_score, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory.id, memory.content, memory.created_at, memory.updated_at,
                    memory.difficulty, memory.stability, memory.retrievability,
                    memory.reps, memory.lapses, memory.last_review, memory.next_review,
                    json.dumps(memory.tags), memory.signal_score, memory.source
                ))

# 全局实例
_vestige = None

def get_vestige() -> VestigeMemory:
    """获取全局Vestige实例"""
    global _vestige
    if _vestige is None:
        _vestige = VestigeMemory()
    return _vestige

if __name__ == "__main__":
    # 测试
    vm = VestigeMemory()
    
    # 添加测试记忆
    m1 = vm.ingest("测试记忆内容1", tags=["test"], signal_score=7.0)
    print(f"添加记忆: {m1.id}")
    
    # 复习
    m1_reviewed = vm.review(m1.id, rating=3)
    print(f"复习后稳定性: {m1_reviewed.stability}")
    
    # 统计
    stats = vm.get_stats()
    print(f"统计: {stats}")
