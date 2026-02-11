#!/usr/bin/env python3
"""
v5.4 主动回忆与预测系统
- 联想提示: 提到A时自动浮现B
- 时机回忆: 特定时间浮现相关记忆
- 模式识别: 学习用户行为模式
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sys

sys.path.insert(0, 'scripts/memory-system')
from vector_memory import get_vector_memory

class ProactiveMemorySystem:
    """主动回忆系统 - 让记忆主动浮现"""
    
    def __init__(self):
        self.vm = get_vector_memory()
        self.memory_patterns_file = "memory/proactive/patterns.json"
        self.time_triggers_file = "memory/proactive/time_triggers.json"
        self.associations_file = "memory/associations/memory_graph.json"
        
        # 确保目录存在
        os.makedirs("memory/proactive", exist_ok=True)
        
        # 加载模式
        self.patterns = self._load_json(self.memory_patterns_file, {})
        self.time_triggers = self._load_json(self.time_triggers_file, [])
        
    def _load_json(self, path: str, default: Any) -> Any:
        """加载JSON文件"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return default
    
    def _save_json(self, path: str, data: Any):
        """保存JSON文件"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def find_associated_memories(self, query: str, top_k: int = 3) -> List[Dict]:
        """联想回忆: 找到与查询相关的关联记忆"""
        # 先搜索相似记忆
        similar = self.vm.search_similar(query, top_k=5)
        
        associated = []
        seen_ids = set()
        
        for mem in similar:
            mem_id = mem['memory_id']
            if mem_id in seen_ids:
                continue
            seen_ids.add(mem_id)
            
            # 找到关联的记忆
            related = self._find_related(mem_id, exclude=seen_ids)
            for rel in related[:2]:  # 每个记忆最多2个关联
                if rel['memory_id'] not in seen_ids:
                    seen_ids.add(rel['memory_id'])
                    associated.append({
                        'trigger': mem['content'][:50],
                        'memory': rel,
                        'association_type': rel.get('relation', 'related'),
                        'similarity': rel.get('similarity', 0)
                    })
        
        return associated[:top_k]
    
    def _find_related(self, memory_id: str, exclude: set) -> List[Dict]:
        """找到与指定记忆相关的其他记忆"""
        # 从关联图中查找
        if not os.path.exists(self.associations_file):
            return []
        
        with open(self.associations_file, 'r') as f:
            graph = json.load(f)
        
        related = []
        for edge in graph.get('edges', []):
            source = edge.get('source', '')
            target = edge.get('target', '')
            
            if source == memory_id and target not in exclude:
                # 找到目标记忆内容
                if target in self.vm.memories:
                    mem = self.vm.memories[target]
                    related.append({
                        'memory_id': target,
                        'content': mem['content'],
                        'relation': edge.get('relation', 'related'),
                        'similarity': edge.get('weight', 0.5)
                    })
            elif target == memory_id and source not in exclude:
                if source in self.vm.memories:
                    mem = self.vm.memories[source]
                    related.append({
                        'memory_id': source,
                        'content': mem['content'],
                        'relation': edge.get('relation', 'related'),
                        'similarity': edge.get('weight', 0.5)
                    })
        
        # 按权重排序
        related.sort(key=lambda x: x['similarity'], reverse=True)
        return related
    
    def check_time_triggers(self) -> List[Dict]:
        """时机回忆: 检查是否有时间触发的记忆"""
        triggered = []
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_date = now.strftime("%Y-%m-%d")
        
        for trigger in self.time_triggers:
            trigger_time = trigger.get('time', '')
            trigger_date = trigger.get('date', '')
            
            # 检查是否匹配
            time_match = (trigger_time == current_time) or self._is_time_near(trigger_time, current_time)
            date_match = (not trigger_date) or (trigger_date == current_date)
            
            if time_match and date_match:
                memory_id = trigger.get('memory_id')
                if memory_id and memory_id in self.vm.memories:
                    triggered.append({
                        'trigger_type': 'time',
                        'trigger_value': trigger_time,
                        'memory': self.vm.memories[memory_id],
                        'reason': trigger.get('reason', 'scheduled')
                    })
        
        return triggered
    
    def _is_time_near(self, trigger_time: str, current_time: str, window_minutes: int = 5) -> bool:
        """检查时间是否在窗口内"""
        try:
            t1 = datetime.strptime(trigger_time, "%H:%M")
            t2 = datetime.strptime(current_time, "%H:%M")
            diff = abs((t2 - t1).total_seconds() / 60)
            return diff <= window_minutes
        except:
            return False
    
    def learn_pattern(self, context: str, action: str, outcome: str):
        """学习用户行为模式"""
        pattern_key = f"{context} -> {action}"
        
        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = {
                'context': context,
                'action': action,
                'count': 0,
                'success': 0,
                'outcomes': [],
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat()
            }
        
        self.patterns[pattern_key]['count'] += 1
        self.patterns[pattern_key]['last_seen'] = datetime.now().isoformat()
        self.patterns[pattern_key]['outcomes'].append({
            'outcome': outcome,
            'time': datetime.now().isoformat()
        })
        
        # 限制 outcomes 数量
        if len(self.patterns[pattern_key]['outcomes']) > 10:
            self.patterns[pattern_key]['outcomes'] = self.patterns[pattern_key]['outcomes'][-10:]
        
        self._save_json(self.memory_patterns_file, self.patterns)
    
    def predict_next_action(self, current_context: str) -> Optional[Dict]:
        """基于模式预测下一步行动"""
        matching_patterns = []
        
        for key, pattern in self.patterns.items():
            if current_context.lower() in pattern['context'].lower():
                matching_patterns.append(pattern)
        
        if not matching_patterns:
            return None
        
        # 按频次排序
        matching_patterns.sort(key=lambda x: x['count'], reverse=True)
        best = matching_patterns[0]
        
        return {
            'predicted_action': best['action'],
            'confidence': min(best['count'] / 5, 0.9),  # 最多90%置信度
            'based_on': best['count'],
            'outcome_history': best['outcomes'][-3:]
        }
    
    def add_time_trigger(self, memory_id: str, time_str: str, reason: str = "", date_str: str = ""):
        """添加时间触发器"""
        trigger = {
            'memory_id': memory_id,
            'time': time_str,
            'date': date_str,
            'reason': reason,
            'created': datetime.now().isoformat()
        }
        
        self.time_triggers.append(trigger)
        self._save_json(self.time_triggers_file, self.time_triggers)
    
    def get_proactive_suggestions(self, current_query: str = "") -> Dict:
        """获取主动建议（综合联想+时机+预测）"""
        suggestions = {
            'associations': [],
            'time_triggers': [],
            'predictions': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # 联想回忆
        if current_query:
            suggestions['associations'] = self.find_associated_memories(current_query)
        
        # 时机回忆
        suggestions['time_triggers'] = self.check_time_triggers()
        
        # 行为预测
        if current_query:
            suggestions['predictions'] = self.predict_next_action(current_query)
        
        return suggestions


def main():
    """命令行测试"""
    pms = ProactiveMemorySystem()
    
    print("=" * 60)
    print("🧠 v5.4 主动回忆系统测试")
    print("=" * 60)
    
    # 测试1: 联想回忆
    print("\n📊 测试1: 联想回忆")
    associations = pms.find_associated_memories("记忆系统", top_k=3)
    for i, assoc in enumerate(associations, 1):
        print(f"   {i}. 触发: {assoc['trigger']}")
        print(f"      关联: {assoc['memory']['content'][:50]}...")
        print(f"      类型: {assoc['association_type']}")
    
    # 测试2: 时机回忆
    print("\n📊 测试2: 时机回忆")
    triggers = pms.check_time_triggers()
    if triggers:
        for t in triggers:
            print(f"   ⏰ {t['trigger_value']}: {t['memory']['content'][:50]}")
    else:
        print("   当前无时间触发")
    
    # 测试3: 行为预测
    print("\n📊 测试3: 行为预测")
    prediction = pms.predict_next_action("进化")
    if prediction:
        print(f"   预测行动: {prediction['predicted_action']}")
        print(f"   置信度: {prediction['confidence']:.1%}")
    else:
        print("   暂无足够模式数据")
    
    print("\n" + "=" * 60)
    print("✅ v5.4 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
