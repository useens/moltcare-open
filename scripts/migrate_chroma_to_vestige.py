#!/usr/bin/env python3
"""
迁移脚本: ChromaDB记忆 → Vestige FSRS记忆
将向量记忆导入FSRS间隔重复系统
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# 添加工作目录到路径
workspace = Path.home() / ".openclaw/workspace"
sys.path.insert(0, str(workspace))

from core.vestige_memory import VestigeMemory, MemoryItem

# 数据库路径
CHROMA_DB_PATH = workspace / "data/vector_memory/memory.db"
VESTIGE_DB_PATH = Path.home() / ".local/share/vestige/vestige.db"

class ChromaToVestigeMigrator:
    """ChromaDB到Vestige的迁移器"""
    
    def __init__(self):
        self.vestige = VestigeMemory()
        self.stats = {
            "total": 0,
            "migrated": 0,
            "skipped": 0,
            "failed": 0
        }
    
    def get_chroma_memories(self) -> list:
        """从ChromaDB获取所有记忆"""
        if not CHROMA_DB_PATH.exists():
            print(f"❌ ChromaDB不存在: {CHROMA_DB_PATH}")
            return []
        
        try:
            conn = sqlite3.connect(CHROMA_DB_PATH)
            cursor = conn.cursor()
            
            # 获取所有文档
            cursor.execute("""
                SELECT id, content, file_path, signal, created_at, updated_at
                FROM documents
            """)
            
            memories = []
            for row in cursor.fetchall():
                memory = {
                    "id": str(row[0]),
                    "content": row[1],
                    "file_path": row[2],
                    "signal": row[3] or 5,
                    "created_at": row[4],
                    "updated_at": row[5],
                    "access_count": 0,  # 此表没有访问次数
                    "last_accessed": None
                }
                memories.append(memory)
            
            conn.close()
            return memories
            
        except Exception as e:
            print(f"❌ 读取ChromaDB失败: {e}")
            return []
    
    def calculate_signal_score(self, memory: dict) -> float:
        """
        根据ChromaDB数据计算Signal评分
        """
        # 直接从数据库获取signal
        signal = memory.get("signal", 5)
        if signal is None:
            signal = 5
        return min(10, max(1, float(signal)))
    
    def calculate_fsrs_params(self, memory: dict) -> dict:
        """
        根据Signal计算FSRS初始参数
        """
        signal = memory.get("signal", 5) or 5
        
        # 根据Signal估算稳定性
        if signal >= 8:
            stability = 30.0
            difficulty = 3.0
        elif signal >= 6:
            stability = 10.0
            difficulty = 4.0
        elif signal >= 4:
            stability = 3.0
            difficulty = 5.0
        else:
            stability = 1.0
            difficulty = 6.0
        
        return {
            "stability": stability,
            "difficulty": difficulty,
            "reps": 0,
            "lapses": 0
        }
    
    def migrate_memory(self, chroma_memory: dict) -> bool:
        """迁移单条记忆"""
        try:
            content = chroma_memory.get("content", "").strip()
            if not content or len(content) < 10:
                self.stats["skipped"] += 1
                return False
            
            # 计算Signal评分
            signal_score = self.calculate_signal_score(chroma_memory)
            
            # 计算FSRS参数
            fsrs_params = self.calculate_fsrs_params(chroma_memory)
            
            # 从file_path提取标签
            file_path = chroma_memory.get("file_path", "")
            tags = []
            if "/memory/" in file_path:
                tags.append("memory")
            elif "/docs/" in file_path:
                tags.append("docs")
            elif "/code/" in file_path:
                tags.append("code")
            
            # 创建Vestige记忆
            memory = self.vestige.ingest(
                content=content,
                tags=tags,
                signal_score=signal_score,
                source="chroma_migration"
            )
            
            # 更新FSRS参数
            # 注意：vestige.ingest会创建新记录，我们需要更新它
            import sqlite3
            with sqlite3.connect(self.vestige.db_path) as conn:
                conn.execute("""
                    UPDATE memories 
                    SET stability = ?, difficulty = ?, reps = ?,
                        created_at = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    fsrs_params["stability"],
                    fsrs_params["difficulty"],
                    fsrs_params["reps"],
                    chroma_memory.get("created_at", datetime.now().isoformat()),
                    chroma_memory.get("updated_at", datetime.now().isoformat()),
                    memory.id
                ))
            
            self.stats["migrated"] += 1
            return True
            
        except Exception as e:
            print(f"  ❌ 迁移失败 {chroma_memory.get('id', 'unknown')}: {e}")
            self.stats["failed"] += 1
            return False
    
    def migrate_all(self, dry_run: bool = False):
        """执行全部迁移"""
        print("=" * 60)
        print("ChromaDB → Vestige 记忆迁移")
        print("=" * 60)
        
        # 获取ChromaDB记忆
        print(f"\n1. 读取ChromaDB...")
        memories = self.get_chroma_memories()
        self.stats["total"] = len(memories)
        print(f"   找到 {len(memories)} 条记忆")
        
        if dry_run:
            print(f"\n2. [演习模式] 预计迁移 {len(memories)} 条记忆")
            return
        
        # 执行迁移
        print(f"\n2. 开始迁移...")
        for i, memory in enumerate(memories, 1):
            if i % 50 == 0:
                print(f"   进度: {i}/{len(memories)} ({self.stats['migrated']} 成功)")
            
            self.migrate_memory(memory)
        
        # 输出统计
        print(f"\n3. 迁移完成")
        print(f"   总计: {self.stats['total']}")
        print(f"   成功: {self.stats['migrated']}")
        print(f"   跳过: {self.stats['skipped']}")
        print(f"   失败: {self.stats['failed']}")
        
        # Vestige统计
        print(f"\n4. Vestige当前状态")
        vestige_stats = self.vestige.get_stats()
        for key, value in vestige_stats.items():
            print(f"   {key}: {value}")
        
        return self.stats

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="迁移ChromaDB记忆到Vestige")
    parser.add_argument("--dry-run", action="store_true", help="演习模式，不实际写入")
    parser.add_argument("--limit", type=int, help="限制迁移数量")
    
    args = parser.parse_args()
    
    migrator = ChromaToVestigeMigrator()
    
    if args.dry_run:
        migrator.migrate_all(dry_run=True)
    else:
        # 确认提示
        print("⚠️  这将把ChromaDB记忆导入Vestige FSRS系统")
        print("是否继续? [y/N] ")
        
        try:
            response = input().strip().lower()
            if response in ('y', 'yes'):
                migrator.migrate_all()
            else:
                print("已取消")
        except EOFError:
            # 非交互模式，直接执行
            print("非交互模式，直接执行迁移...")
            migrator.migrate_all()

if __name__ == "__main__":
    main()
