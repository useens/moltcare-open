#!/usr/bin/env python3
"""
向量记忆系统 v5.3 - 记忆遗忘与压缩
扩展v5.2，添加遗忘机制保持系统轻盈
"""

import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pickle
import hashlib

# 路径配置
WORKSPACE = Path("/root/.openclaw/workspace")
VECTOR_DIR = WORKSPACE / "memory/vector"
VECTOR_FILE = VECTOR_DIR / "memory_vectors.pkl"
ARCHIVE_FILE = VECTOR_DIR / "archived_memories.pkl"
COMPRESSION_LOG = VECTOR_DIR / "compression_log.json"

# 遗忘阈值配置
FORGET_CONFIG = {
    "decay_days": 30,          # 30天未访问开始衰减
    "archive_threshold": 3.0,   # 价值<3归档
    "delete_threshold": 1.0,    # 价值<1删除（极少发生）
    "protected_types": ["user_pref", "core_identity", "safety_rule"],  # 永不遗忘
    "compression_similarity": 0.85,  # 相似度>0.85合并
    "min_compression_items": 3,      # 最少3条才合并
}


class MemoryValueCalculator:
    """记忆价值计算器 - v5.3核心"""
    
    @staticmethod
    def calculate(memory: Dict, current_time: datetime = None) -> float:
        """
        计算记忆当前价值
        
        公式: (基础重要性 * 时间衰减) + 访问频率加分
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 基础分 (1-10)
        base = memory.get("importance", 5)
        
        # 检查是否受保护类型
        mem_type = memory.get("type", "general")
        if mem_type in FORGET_CONFIG["protected_types"]:
            return 10.0  # 永不高价值记忆
        
        # 时间衰减
        created_at = datetime.fromisoformat(memory.get("created_at", current_time.isoformat()))
        age_days = (current_time - created_at).days
        time_decay = max(0.1, 1 - (age_days / FORGET_CONFIG["decay_days"]))
        
        # 访问频率加分
        access_count = memory.get("access_count", 0)
        last_accessed = memory.get("last_accessed")
        
        access_bonus = 0
        if last_accessed:
            last_access = datetime.fromisoformat(last_accessed)
            days_since_access = (current_time - last_access).days
            
            # 近期访问有额外加分
            if days_since_access < 7:
                access_bonus = min(access_count * 0.2, 3.0)
            elif days_since_access < 30:
                access_bonus = min(access_count * 0.1, 2.0)
        
        # 最终价值
        value = (base * time_decay) + access_bonus
        return min(value, 10.0)  # 最高10分
    
    @staticmethod
    def should_archive(memory: Dict, current_time: datetime = None) -> bool:
        """判断是否应该归档"""
        value = MemoryValueCalculator.calculate(memory, current_time)
        return value < FORGET_CONFIG["archive_threshold"]
    
    @staticmethod
    def should_delete(memory: Dict, current_time: datetime = None) -> bool:
        """判断是否应该删除（极少发生）"""
        value = MemoryValueCalculator.calculate(memory, current_time)
        mem_type = memory.get("type", "general")
        
        # 受保护类型永不删除
        if mem_type in FORGET_CONFIG["protected_types"]:
            return False
        
        return value < FORGET_CONFIG["delete_threshold"]


class MemoryCompressor:
    """记忆压缩器 - 合并相似记忆"""
    
    def __init__(self, vector_memory_instance):
        self.vms = vector_memory_instance
    
    def find_similar_groups(self, min_similarity: float = None) -> List[List[str]]:
        """查找相似记忆组"""
        if min_similarity is None:
            min_similarity = FORGET_CONFIG["compression_similarity"]
        
        memories = self.vms.memories
        if len(memories) < FORGET_CONFIG["min_compression_items"]:
            return []
        
        # 构建相似度矩阵
        memory_ids = list(memories.keys())
        groups = []
        processed = set()
        
        for i, mid1 in enumerate(memory_ids):
            if mid1 in processed:
                continue
            
            group = [mid1]
            emb1 = memories[mid1]["embedding"]
            
            for mid2 in memory_ids[i+1:]:
                if mid2 in processed:
                    continue
                
                emb2 = memories[mid2]["embedding"]
                similarity = self._cosine_similarity(emb1, emb2)
                
                if similarity >= min_similarity:
                    group.append(mid2)
            
            if len(group) >= FORGET_CONFIG["min_compression_items"]:
                groups.append(group)
                processed.update(group)
        
        return groups
    
    def compress_group(self, group: List[str]) -> Optional[Dict]:
        """压缩一组相似记忆为摘要"""
        if len(group) < FORGET_CONFIG["min_compression_items"]:
            return None
        
        memories = self.vms.memories
        
        # 收集组内记忆内容
        contents = []
        sources = []
        tags = set()
        total_importance = 0
        oldest_time = datetime.now()
        
        for mid in group:
            mem = memories.get(mid, {})
            contents.append(mem.get("content", ""))
            sources.append(mem.get("source", ""))
            tags.update(mem.get("tags", []))
            total_importance += mem.get("importance", 5)
            
            created = datetime.fromisoformat(mem.get("created_at", datetime.now().isoformat()))
            if created < oldest_time:
                oldest_time = created
        
        # 生成摘要（简化版，实际可用LLM生成）
        summary = self._generate_summary(contents)
        
        # 生成新ID
        combined = "".join(group)
        new_id = f"compressed_{hashlib.md5(combined.encode()).hexdigest()[:8]}"
        
        compressed_memory = {
            "id": new_id,
            "content": summary,
            "source": " | ".join(filter(None, sources))[:200],
            "type": "compressed",
            "importance": min(total_importance // len(group) + 1, 10),
            "tags": list(tags) + ["compressed", "auto_summary"],
            "created_at": oldest_time.isoformat(),
            "compressed_from": group,
            "compression_count": len(group),
            "compression_date": datetime.now().isoformat(),
        }
        
        return compressed_memory
    
    def _generate_summary(self, contents: List[str]) -> str:
        """生成内容摘要（简化版）"""
        if not contents:
            return ""
        
        # 找到共同关键词（简单实现）
        common_prefix = self._find_common_prefix(contents)
        
        if len(contents) == 1:
            return contents[0]
        
        summary = f"[合并{len(contents)}条相关记忆] "
        
        if common_prefix:
            summary += f"关于{common_prefix}的系列记录: "
        
        # 提取每条的关键点
        key_points = []
        for i, content in enumerate(contents[:3], 1):  # 最多显示3条
            # 取前50字符
            key_points.append(f"{i}.{content[:50]}...")
        
        summary += " | ".join(key_points)
        
        if len(contents) > 3:
            summary += f" 等共{len(contents)}条"
        
        return summary
    
    def _find_common_prefix(self, contents: List[str]) -> str:
        """找到共同前缀"""
        if not contents:
            return ""
        
        # 简单实现：找前10字符相同的
        first = contents[0][:10]
        for content in contents[1:]:
            if not content.startswith(first):
                return ""
        return first
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


class MemoryForgettingSystem:
    """记忆遗忘系统 - v5.3主控"""
    
    def __init__(self):
        self.vector_file = VECTOR_FILE
        self.archive_file = ARCHIVE_FILE
        self.compression_log = COMPRESSION_LOG
        
        # 加载数据
        self.memories = self._load_vectors()
        self.archived = self._load_archived()
        self.compression_history = self._load_compression_log()
        
        # 子系统
        self.value_calc = MemoryValueCalculator()
        self.compressor = MemoryCompressor(self)
    
    def _load_vectors(self) -> Dict[str, Dict]:
        """加载活跃记忆"""
        if self.vector_file.exists():
            with open(self.vector_file, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _load_archived(self) -> Dict[str, Dict]:
        """加载归档记忆"""
        if self.archive_file.exists():
            with open(self.archive_file, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _load_compression_log(self) -> List[Dict]:
        """加载压缩历史"""
        if self.compression_log.exists():
            with open(self.compression_log, 'r') as f:
                return json.load(f)
        return []
    
    def _save_all(self):
        """保存所有数据"""
        with open(self.vector_file, 'wb') as f:
            pickle.dump(self.memories, f)
        
        with open(self.archive_file, 'wb') as f:
            pickle.dump(self.archived, f)
        
        with open(self.compression_log, 'w') as f:
            json.dump(self.compression_history, f, indent=2)
    
    def run_maintenance(self, dry_run: bool = False) -> Dict:
        """
        执行记忆维护（遗忘+压缩）
        
        Returns:
            维护报告
        """
        print("🔧 开始记忆系统维护 v5.3")
        print("=" * 50)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "scanned": len(self.memories),
            "archived": [],
            "deleted": [],
            "compressed": [],
            "values": {}
        }
        
        # 步骤1: 计算所有记忆价值
        print("\n📊 步骤1: 评估记忆价值...")
        for mid, memory in list(self.memories.items()):
            value = self.value_calc.calculate(memory)
            report["values"][mid] = round(value, 2)
            memory["current_value"] = value
        
        # 步骤2: 归档低价值记忆
        print("\n📦 步骤2: 归档低价值记忆...")
        to_archive = []
        for mid, memory in list(self.memories.items()):
            if self.value_calc.should_archive(memory):
                to_archive.append(mid)
        
        for mid in to_archive:
            memory = self.memories.pop(mid)
            memory["archived_at"] = datetime.now().isoformat()
            memory["archive_reason"] = "low_value"
            self.archived[mid] = memory
            report["archived"].append(mid)
            print(f"  📦 归档: {mid[:30]}... (价值: {memory.get('current_value', 0):.2f})")
        
        # 步骤3: 压缩相似记忆
        print("\n🗜️ 步骤3: 压缩相似记忆...")
        similar_groups = self.compressor.find_similar_groups()
        
        for group in similar_groups:
            compressed = self.compressor.compress_group(group)
            if compressed:
                # 删除原记忆
                for mid in group:
                    if mid in self.memories:
                        del self.memories[mid]
                
                # 添加压缩记忆（需要重新向量化）
                from vector_memory import get_vector_memory
                vms = get_vector_memory()
                
                # 为新摘要生成向量
                embedding = vms._get_embedding(compressed["content"])
                compressed["embedding"] = embedding
                
                new_id = compressed["id"]
                self.memories[new_id] = compressed
                
                report["compressed"].append({
                    "new_id": new_id,
                    "merged": group,
                    "count": len(group)
                })
                
                self.compression_history.append({
                    "date": datetime.now().isoformat(),
                    "new_id": new_id,
                    "merged_ids": group,
                    "summary": compressed["content"][:100]
                })
                
                print(f"  🗜️ 压缩: {len(group)}条 → {new_id}")
        
        # 步骤4: 保存结果
        if not dry_run:
            self._save_all()
            print("\n💾 保存完成")
        
        # 生成统计
        report["active_after"] = len(self.memories)
        report["archived_total"] = len(self.archived)
        
        print("\n" + "=" * 50)
        print("✅ 维护完成")
        print(f"   扫描: {report['scanned']}条")
        print(f"   归档: {len(report['archived'])}条")
        print(f"   压缩: {len(report['compressed'])}组")
        print(f"   活跃: {report['active_after']}条")
        print(f"   归档库: {report['archived_total']}条")
        
        return report
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计"""
        return {
            "active_memories": len(self.memories),
            "archived_memories": len(self.archived),
            "total_memories": len(self.memories) + len(self.archived),
            "compression_history": len(self.compression_history),
            "archive_file_size_mb": round(self.archive_file.stat().st_size / 1024 / 1024, 2) if self.archive_file.exists() else 0,
            "vector_file_size_mb": round(self.vector_file.stat().st_size / 1024 / 1024, 2) if self.vector_file.exists() else 0,
        }
    
    def search_with_archive(self, query: str, include_archived: bool = False) -> List[Dict]:
        """搜索记忆（可选择包含归档）"""
        from vector_memory import get_vector_memory
        vms = get_vector_memory()
        
        results = vms.search_similar(query)
        
        if include_archived and self.archived:
            # 在归档中搜索（简化实现）
            print(f"\n📦 归档库中有 {len(self.archived)} 条历史记忆")
        
        return results


def run_forgetting_maintenance(dry_run: bool = False):
    """运行遗忘维护（命令行入口）"""
    fsys = MemoryForgettingSystem()
    report = fsys.run_maintenance(dry_run=dry_run)
    return report


def show_memory_stats():
    """显示记忆统计"""
    fsys = MemoryForgettingSystem()
    stats = fsys.get_memory_stats()
    
    print("📊 记忆系统统计 v5.3")
    print("=" * 40)
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        show_memory_stats()
    elif len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        run_forgetting_maintenance(dry_run=True)
    else:
        run_forgetting_maintenance(dry_run=False)
