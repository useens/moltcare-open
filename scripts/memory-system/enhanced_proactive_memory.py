#!/usr/bin/env python3
"""
v5.4 增强版 - 主动回忆与预测
- 基于长期记忆的联想
- 时间模式学习
- 行为预测
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sys

sys.path.insert(0, 'scripts/memory-system')
from vector_memory import get_vector_memory

class EnhancedProactiveMemory:
    """增强版主动回忆系统"""
    
    def __init__(self):
        self.memory_dir = "memory"
        self.proactive_dir = f"{self.memory_dir}/proactive"
        self.patterns_file = f"{self.proactive_dir}/patterns.json"
        self.time_triggers_file = f"{self.proactive_dir}/time_triggers.json"
        
        os.makedirs(self.proactive_dir, exist_ok=True)
        
        # 加载数据
        self.patterns = self._load_json(self.patterns_file, {})
        self.time_triggers = self._load_json(self.time_triggers_file, [])
        
        # 加载长期记忆
        self.long_term = self._load_json(
            f"{self.memory_dir}/long_term_memories.json", []
        )
        self.associations = self._load_json(
            f"{self.memory_dir}/associations/memory_graph.json",
            {'nodes': [], 'edges': []}
        )
        
        self.vm = get_vector_memory()
    
    def _load_json(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return default
    
    def _save_json(self, path: str, data: Any):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def learn_from_long_term(self):
        """从长期记忆学习模式"""
        print("📚 从长期记忆学习模式...")
        
        # 学习分类模式
        category_patterns = {}
        for mem in self.long_term:
            cat = mem.get('category', '其他')
            if cat not in category_patterns:
                category_patterns[cat] = []
            category_patterns[cat].append(mem['content'])
        
        # 保存模式
        for cat, contents in category_patterns.items():
            self.patterns[f"category_{cat}"] = {
                'type': 'category',
                'category': cat,
                'count': len(contents),
                'keywords': self._extract_common_keywords(contents),
                'last_updated': datetime.now().isoformat()
            }
        
        print(f"  学习 {len(category_patterns)} 个分类模式")
        
        # 学习时间模式
        self._learn_time_patterns()
        
        self._save_json(self.patterns_file, self.patterns)
    
    def _extract_common_keywords(self, contents: List[str]) -> List[str]:
        """提取共同关键词"""
        all_keywords = []
        for c in contents:
            words = re.findall(r'[a-zA-Z_]+|\d+%|v\d+\.\d+|GitHub|Moltbook', c)
            all_keywords.extend(words)
        
        # 统计频率
        from collections import Counter
        counter = Counter(all_keywords)
        return [w for w, c in counter.most_common(10)]
    
    def _learn_time_patterns(self):
        """学习时间模式"""
        print("⏰ 学习时间模式...")
        
        # 分析长期记忆的时间分布
        hours = {}
        for mem in self.long_term:
            created = mem.get('created_at', '')
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    hour = dt.hour
                    hours[hour] = hours.get(hour, 0) + 1
                except:
                    pass
        
        # 找出活跃时段
        if hours:
            peak_hour = max(hours.items(), key=lambda x: x[1])[0]
            self.patterns['time_preference'] = {
                'type': 'time',
                'peak_hour': peak_hour,
                'hour_distribution': hours,
                'suggestion': f'用户在{peak_hour}:00时段最活跃'
            }
            print(f"  发现活跃时段: {peak_hour}:00")
    
    def build_enhanced_associations(self) -> List[Dict]:
        """构建增强版关联"""
        print("🔗 构建增强版联想...")
        
        associations = []
        
        # 1. 基于关联图谱的联想
        for edge in self.associations.get('edges', []):
            source = edge.get('source')
            target = edge.get('target')
            
            # 查找记忆内容
            source_mem = next((m for m in self.long_term if m['id'] == source), None)
            target_mem = next((m for m in self.long_term if m['id'] == target), None)
            
            if source_mem and target_mem:
                associations.append({
                    'trigger': source_mem['content'][:50],
                    'suggested': target_mem['content'][:50],
                    'type': 'graph_association',
                    'weight': edge.get('weight', 0.5),
                    'relation': 'related'
                })
        
        # 2. 基于分类的联想
        category_memories = {}
        for mem in self.long_term:
            cat = mem.get('category', '其他')
            if cat not in category_memories:
                category_memories[cat] = []
            category_memories[cat].append(mem)
        
        for cat, memories in category_memories.items():
            if len(memories) >= 2:
                # 同一分类下的记忆相互联想
                for i, m1 in enumerate(memories[:3]):
                    for m2 in memories[i+1:4]:
                        associations.append({
                            'trigger': m1['content'][:50],
                            'suggested': m2['content'][:50],
                            'type': 'category_association',
                            'category': cat,
                            'weight': 0.6
                        })
        
        print(f"  构建 {len(associations)} 条联想")
        return associations
    
    def add_smart_time_triggers(self):
        """添加智能时间触发器"""
        print("⏰ 添加智能时间触发器...")
        
        triggers = []
        
        # 基于记忆重要性的时间触发
        high_importance = [m for m in self.long_term if m.get('importance', 5) >= 8]
        
        for i, mem in enumerate(high_importance[:5]):
            # 为重要记忆设置回顾提醒
            trigger_time = f"{9 + i}:00"  # 分散在上午
            triggers.append({
                'memory_id': mem['id'],
                'time': trigger_time,
                'reason': f'重要记忆回顾: {mem["category"]}',
                'created': datetime.now().isoformat()
            })
        
        self.time_triggers = triggers
        self._save_json(self.time_triggers_file, self.time_triggers)
        
        print(f"  添加 {len(triggers)} 个时间触发器")
    
    def get_proactive_suggestions(self, query: str = "") -> Dict:
        """获取主动建议"""
        suggestions = {
            'query': query,
            'associations': [],
            'patterns': [],
            'time_triggers': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. 基于查询的联想
        if query:
            # 查找相关的长期记忆
            for mem in self.long_term[:10]:
                # 简单关键词匹配
                if any(kw.lower() in query.lower() for kw in mem.get('keywords', [])):
                    suggestions['associations'].append({
                        'memory': mem['content'][:100],
                        'category': mem['category'],
                        'importance': mem['importance']
                    })
        
        # 2. 推荐模式
        if self.patterns:
            for key, pattern in list(self.patterns.items())[:3]:
                if pattern.get('type') == 'category':
                    suggestions['patterns'].append({
                        'category': pattern['category'],
                        'count': pattern['count'],
                        'keywords': pattern.get('keywords', [])[:5]
                    })
        
        # 3. 检查时间触发
        current_time = datetime.now().strftime("%H:%M")
        for trigger in self.time_triggers:
            if trigger.get('time', '') == current_time[:5]:
                mem = next((m for m in self.long_term if m['id'] == trigger['memory_id']), None)
                if mem:
                    suggestions['time_triggers'].append({
                        'time': trigger['time'],
                        'memory': mem['content'][:80],
                        'reason': trigger['reason']
                    })
        
        return suggestions
    
    def enhance(self):
        """执行增强"""
        print("\n" + "="*60)
        print("🧠 v5.4 增强版 - 主动回忆系统")
        print("="*60)
        
        if not self.long_term:
            print("❌ 长期记忆为空，请先运行v5.1整理")
            return
        
        # 1. 学习模式
        self.learn_from_long_term()
        
        # 2. 构建增强联想
        associations = self.build_enhanced_associations()
        
        # 3. 添加时间触发
        self.add_smart_time_triggers()
        
        # 4. 测试主动建议
        print("\n🧪 测试主动建议...")
        test_suggestions = self.get_proactive_suggestions("记忆系统")
        print(f"  联想结果: {len(test_suggestions['associations'])} 条")
        print(f"  模式推荐: {len(test_suggestions['patterns'])} 个")
        
        print("\n" + "="*60)
        print("✅ v5.4 增强完成")
        print("="*60)
        
        return {
            'patterns_learned': len(self.patterns),
            'associations_built': len(associations),
            'time_triggers': len(self.time_triggers)
        }


def main():
    """执行增强"""
    proactive = EnhancedProactiveMemory()
    result = proactive.enhance()
    
    if result:
        print(f"\n📈 增强成果:")
        print(f"  学习模式: {result['patterns_learned']} 个")
        print(f"  联想关联: {result['associations_built']} 条")
        print(f"  时间触发: {result['time_triggers']} 个")


if __name__ == "__main__":
    main()
