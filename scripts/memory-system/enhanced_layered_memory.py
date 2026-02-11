#!/usr/bin/env python3
"""
v5.1 增强版 - 长期记忆自动构建
- 自动提取核心记忆
- 构建高质量关联
- 智能分层存储
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys

sys.path.insert(0, 'scripts/memory-system')
from vector_memory import get_vector_memory

class EnhancedLayeredMemory:
    """增强版分层记忆系统"""
    
    def __init__(self):
        self.memory_dir = "memory"
        self.long_term_file = f"{self.memory_dir}/long_term_memories.json"
        self.associations_file = f"{self.memory_dir}/associations/memory_graph.json"
        
        # 确保目录存在
        os.makedirs(f"{self.memory_dir}/associations", exist_ok=True)
        
        # 加载现有数据
        self.long_term = self._load_json(self.long_term_file, [])
        self.associations = self._load_json(self.associations_file, {'nodes': [], 'edges': []})
        
        self.vm = get_vector_memory()
    
    def _load_json(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return default
    
    def _save_json(self, path: str, data: Any):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def extract_core_memories(self) -> List[Dict]:
        """从向量记忆中提取核心记忆"""
        print("🔍 分析向量记忆库...")
        
        core_memories = []
        
        for mid, mem in self.vm.memories.items():
            content = mem.get('content', '')
            importance = self._calculate_importance(content)
            
            # 只保留高价值记忆
            if importance >= 7:
                core_memories.append({
                    'id': mid,
                    'content': content,
                    'importance': importance,
                    'category': self._categorize(content),
                    'keywords': self._extract_keywords(content),
                    'created_at': mem.get('created_at', datetime.now().isoformat()),
                    'vector_id': mid
                })
        
        # 按重要性排序
        core_memories.sort(key=lambda x: x['importance'], reverse=True)
        
        print(f"  发现 {len(core_memories)} 条核心记忆")
        return core_memories[:100]  # 最多100条
    
    def _calculate_importance(self, content: str) -> int:
        """计算记忆重要性"""
        score = 5  # 基础分
        
        # 关键词加分
        high_value_keywords = [
            'v5.', 'v6.', '版本', '发布', '里程碑',
            '用户授权', 'zxl', '自主', '决策',
            '多代理', 'VM', '双节点', '架构',
            '向量', '记忆系统', '进化',
            'GitHub', 'Moltbook', '深度学习'
        ]
        
        for kw in high_value_keywords:
            if kw.lower() in content.lower():
                score += 1
        
        # 长度适中加分（有实质内容）
        if 50 < len(content) < 500:
            score += 1
        
        # 包含数据和指标加分
        if re.search(r'\d+%|\d+条|\d+个', content):
            score += 1
        
        return min(score, 10)
    
    def _categorize(self, content: str) -> str:
        """分类记忆"""
        categories = {
            '版本发布': ['v5.', 'v6.', '发布', '版本'],
            '用户授权': ['用户', '授权', 'zxl', '自主', '决策'],
            '技术架构': ['多代理', 'VM', '双节点', '架构', '向量'],
            '学习进化': ['学习', '进化', 'GitHub', 'Moltbook'],
            '系统监控': ['健康', '监控', '备份', '故障'],
            '任务执行': ['任务', '执行', '完成', '测试']
        }
        
        for cat, keywords in categories.items():
            if any(kw in content for kw in keywords):
                return cat
        
        return '其他'
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        # 简单关键词提取
        words = re.findall(r'[a-zA-Z_]+|\d+%|\d+条|\d+个|v\d+\.\d+|GitHub|Moltbook', content)
        return list(set(words))[:10]
    
    def build_associations(self, memories: List[Dict]) -> Dict:
        """构建记忆关联"""
        print("🔗 构建记忆关联...")
        
        nodes = [{'id': m['id'], 'content': m['content'][:100]} for m in memories]
        edges = []
        
        # 基于关键词相似度构建关联
        for i, m1 in enumerate(memories):
            for j, m2 in enumerate(memories[i+1:], i+1):
                # 计算关键词重叠
                common = set(m1['keywords']) & set(m2['keywords'])
                if common:
                    similarity = len(common) / max(len(m1['keywords']), len(m2['keywords']))
                    if similarity >= 0.3:  # 至少30%关键词重叠
                        edges.append({
                            'source': m1['id'],
                            'target': m2['id'],
                            'relation': 'related',
                            'weight': round(similarity, 2),
                            'common_keywords': list(common)
                        })
        
        print(f"  构建 {len(edges)} 条关联")
        return {'nodes': nodes, 'edges': edges}
    
    def consolidate(self):
        """执行记忆整理"""
        print("\n" + "="*60)
        print("🧠 v5.1 增强版 - 长期记忆整理")
        print("="*60)
        
        # 1. 提取核心记忆
        core_memories = self.extract_core_memories()
        
        if not core_memories:
            print("⚠️ 未找到核心记忆")
            return
        
        # 2. 构建关联
        associations = self.build_associations(core_memories)
        
        # 3. 保存长期记忆
        self.long_term = core_memories
        self._save_json(self.long_term_file, self.long_term)
        print(f"\n💾 保存 {len(core_memories)} 条长期记忆")
        
        # 4. 保存关联
        self.associations = associations
        self._save_json(self.associations_file, self.associations)
        print(f"💾 保存 {len(associations['edges'])} 条关联")
        
        # 5. 生成分类统计
        categories = {}
        for m in core_memories:
            cat = m['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n📊 记忆分类统计:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}条")
        
        print("\n" + "="*60)
        print("✅ v5.1 整理完成")
        print("="*60)
        
        return {
            'core_memories': len(core_memories),
            'associations': len(associations['edges']),
            'categories': categories
        }


def main():
    """执行整理"""
    layered = EnhancedLayeredMemory()
    result = layered.consolidate()
    
    if result:
        print(f"\n📈 整理成果:")
        print(f"  核心记忆: {result['core_memories']} 条")
        print(f"  记忆关联: {result['associations']} 条")


if __name__ == "__main__":
    main()
