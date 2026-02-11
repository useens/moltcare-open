#!/usr/bin/env python3
"""
记忆遗忘与压缩系统 v5.3
像人类一样遗忘，保持系统轻盈
"""

import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent))
from vector_memory import get_vector_memory

# 配置
FORGET_THRESHOLD = 3.0      # 价值低于此值遗忘
ARCHIVE_THRESHOLD = 5.0     # 价值低于此值归档
COMPRESS_THRESHOLD = 6      # 相似记忆超过此数量压缩
MAX_ACTIVE_MEMORIES = 200   # 活跃记忆上限

class MemoryForgettingSystem:
    """记忆遗忘系统 - v5.3"""
    
    def __init__(self):
        self.vms = get_vector_memory()
        self.vector_file = Path("/root/.openclaw/workspace/memory/vector/memory_vectors.pkl")
        self.archive_dir = Path("/root/.openclaw/workspace/memory/archive")
        self.archive_dir.mkdir(exist_ok=True)
        
    def calculate_memory_value(self, memory: Dict) -> float:
        """
        计算记忆价值 (0-10)
        基础分 × 时间衰减 + 访问加分
        """
        # 基础重要性 (1-10)
        base = memory.get("importance", 5)
        
        # 时间衰减
        created = datetime.fromisoformat(memory.get("created_at", datetime.now().isoformat()))
        age_days = (datetime.now() - created).days
        time_decay = max(0.3, 1 - (age_days / 30))  # 30天后保留30%
        
        # 访问频率加分
        access_count = memory.get("access_count", 0)
        access_bonus = min(access_count * 0.2, 2.0)  # 最多加2分
        
        # 用户指令永不忘
        if memory.get("type") == "user_pref":
            return 10.0
        
        # 里程碑永不忘
        if memory.get("type") == "milestone":
            return 9.0
        
        value = (base * time_decay) + access_bonus
        return min(value, 10.0)
    
    def find_similar_memories(self, memory_id: str, threshold: float = 0.85) -> List[str]:
        """查找相似记忆"""
        if memory_id not in self.vms.memories:
            return []
        
        target = self.vms.memories[memory_id]
        target_embedding = target["embedding"]
        
        similar = []
        for mid, mem in self.vms.memories.items():
            if mid == memory_id:
                continue
            
            # 计算余弦相似度
            embedding = mem["embedding"]
            similarity = np.dot(target_embedding, embedding) / (
                np.linalg.norm(target_embedding) * np.linalg.norm(embedding)
            )
            
            if similarity >= threshold:
                similar.append((mid, similarity))
        
        similar.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in similar]
    
    def compress_similar_memories(self, memory_ids: List[str]) -> Dict:
        """压缩相似记忆为摘要"""
        if len(memory_ids) < 2:
            return None
        
        contents = []
        for mid in memory_ids:
            if mid in self.vms.memories:
                contents.append(self.vms.memories[mid]["content"])
        
        if not contents:
            return None
        
        # 生成摘要（简化版：合并主题）
        summary = f"[压缩 {len(contents)} 条相似记忆] " + contents[0][:100] + "..."
        
        return {
            "id": f"compressed_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "content": summary,
            "compressed_count": len(contents),
            "original_ids": memory_ids,
            "created_at": datetime.now().isoformat(),
            "type": "compressed",
            "importance": max(self.vms.memories[mid].get("importance", 5) for mid in memory_ids if mid in self.vms.memories)
        }
    
    def archive_memory(self, memory_id: str):
        """归档记忆到冷存储"""
        if memory_id not in self.vms.memories:
            return False
        
        memory = self.vms.memories[memory_id]
        
        # 保存到归档文件
        archive_file = self.archive_dir / f"archived_{datetime.now().strftime('%Y%m')}.json"
        
        archived = []
        if archive_file.exists():
            with open(archive_file, 'r') as f:
                archived = json.load(f)
        
        # 添加归档信息
        memory["archived_at"] = datetime.now().isoformat()
        archived.append(memory)
        
        with open(archive_file, 'w') as f:
            json.dump(archived, f, indent=2)
        
        # 从活跃记忆删除
        del self.vms.memories[memory_id]
        self.vms._save_vectors()
        
        return True
    
    def forget_memory(self, memory_id: str):
        """永久遗忘记忆（极少使用）"""
        if memory_id in self.vms.memories:
            del self.vms.memories[memory_id]
            self.vms._save_vectors()
            return True
        return False
    
    def run_forgetting_cycle(self) -> Dict:
        """
        执行遗忘周期
        返回统计信息
        """
        stats = {
            "total_memories": len(self.vms.memories),
            "value_calculated": 0,
            "archived": 0,
            "compressed_groups": 0,
            "compressed_total": 0,
            "forgotten": 0
        }
        
        print("🧠 开始记忆遗忘周期 v5.3")
        print("=" * 50)
        
        # 1. 计算所有记忆的价值
        memory_values = {}
        for mid, memory in self.vms.memories.items():
            value = self.calculate_memory_value(memory)
            memory_values[mid] = value
            stats["value_calculated"] += 1
        
        # 2. 归档低价值记忆
        to_archive = [mid for mid, value in memory_values.items() 
                      if value < ARCHIVE_THRESHOLD and value >= FORGET_THRESHOLD]
        
        for mid in to_archive:
            if self.archive_memory(mid):
                stats["archived"] += 1
                print(f"  📦 归档: {mid[:20]}... (价值: {memory_values[mid]:.2f})")
        
        # 3. 压缩相似记忆
        compressed_ids = set()
        for mid in list(self.vms.memories.keys()):
            if mid in compressed_ids:
                continue
            
            similar = self.find_similar_memories(mid)
            if len(similar) >= COMPRESS_THRESHOLD:
                group = [mid] + similar
                compressed = self.compress_similar_memories(group)
                
                if compressed:
                    # 添加压缩记忆
                    self.vms.add_memory(
                        memory_id=compressed["id"],
                        content=compressed["content"],
                        memory_type="compressed",
                        importance=compressed["importance"]
                    )
                    
                    # 删除原记忆
                    for old_id in group:
                        if old_id in self.vms.memories:
                            del self.vms.memories[old_id]
                            compressed_ids.add(old_id)
                    
                    stats["compressed_groups"] += 1
                    stats["compressed_total"] += len(group)
                    print(f"  🗜️  压缩: {len(group)} 条记忆 → {compressed['id'][:20]}...")
        
        # 4. 遗忘极低价值记忆（慎重）
        to_forget = [mid for mid, value in memory_values.items() 
                     if value < FORGET_THRESHOLD and mid not in compressed_ids]
        
        for mid in to_forget[:10]:  # 每次最多遗忘10条
            if self.forget_memory(mid):
                stats["forgotten"] += 1
                print(f"  🗑️ 遗忘: {mid[:20]}... (价值: {memory_values[mid]:.2f})")
        
        # 5. 保存
        self.vms._save_vectors()
        
        stats["remaining"] = len(self.vms.memories)
        
        print("=" * 50)
        print(f"📊 遗忘周期完成")
        print(f"   计算价值: {stats['value_calculated']} 条")
        print(f"   归档: {stats['archived']} 条")
        print(f"   压缩: {stats['compressed_groups']} 组 ({stats['compressed_total']} 条)")
        print(f"   遗忘: {stats['forgotten']} 条")
        print(f"   剩余: {stats['remaining']} 条")
        
        return stats


def test_forgetting():
    """测试遗忘系统"""
    print("\n🧪 测试记忆遗忘系统 v5.3")
    print("=" * 50)
    
    fsys = MemoryForgettingSystem()
    
    # 运行遗忘周期
    stats = fsys.run_forgetting_cycle()
    
    print("\n✅ 测试完成")
    return stats


if __name__ == "__main__":
    test_forgetting()
