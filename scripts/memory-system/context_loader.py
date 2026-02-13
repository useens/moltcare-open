#!/usr/bin/env python3
"""
上下文感知记忆加载器 - v5.1
根据当前对话主题，自动加载相关记忆
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent))
from layered_memory import get_memory_system, MemoryEntry


class ContextAwareMemoryLoader:
    """上下文感知记忆加载器"""
    
    def __init__(self):
        self.ms = get_memory_system()
        self.context_keywords = []
        
    def extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词（简化版）"""
        # 定义重要关键词列表
        important_keywords = [
            # 系统相关
            "进化", "memory", "记忆", "agent", "代理", "VM", "协作",
            # 技术相关
            "深度学习", "向量", "数据库", "脚本", "任务",
            # 用户相关
            "zxl", "用户", "配置", "备份",
            # 状态相关
            "健康", "状态", "监控", "故障",
        ]
        
        found = []
        text_lower = text.lower()
        for kw in important_keywords:
            if kw.lower() in text_lower:
                found.append(kw)
        
        return found
    
    def load_relevant_memories(self, user_message: str, 
                               max_results: int = 5) -> str:
        """
        加载与当前对话相关的记忆
        返回格式化的记忆文本
        """
        # 提取关键词
        keywords = self.extract_keywords(user_message)
        
        if not keywords:
            # 如果没有关键词，加载最近的重要记忆
            return self._load_recent_important()
        
        # 使用关键词搜索记忆
        all_results = []
        for kw in keywords:
            results = self.ms.context_aware_retrieval(kw, max_results=3)
            all_results.extend(results)
        
        # 去重并排序
        seen_ids = set()
        unique_results = []
        for r in all_results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique_results.append(r)
        
        unique_results.sort(key=lambda x: x.importance, reverse=True)
        
        # 获取关联记忆
        final_results = []
        for r in unique_results[:max_results]:
            final_results.append(r)
            # 添加1-2条关联记忆
            related_ids = self.ms.get_related_memories(r.id)
            for rid in related_ids[:2]:
                # 这里简化处理，实际应该从长期记忆中获取
                pass
        
        # 格式化为文本
        return self._format_memories(final_results[:max_results])
    
    def _load_recent_important(self, limit: int = 5) -> str:
        """加载最近的重要记忆"""
        # 从长期记忆中获取重要性>=8的记忆
        results = self.ms.search_long_term("", min_importance=8)
        
        # 按时间排序，取最近的
        results.sort(key=lambda x: x.created_at, reverse=True)
        
        return self._format_memories(results[:limit])
    
    def _format_memories(self, memories: List[MemoryEntry]) -> str:
        """将记忆格式化为文本"""
        if not memories:
            return ""
        
        lines = ["\n[相关记忆]"]
        
        for i, m in enumerate(memories, 1):
            # 根据类型选择图标
            icon = "📝"
            if m.type == "decision":
                icon = "✅"
            elif m.type == "user_pref":
                icon = "👤"
            elif m.type == "milestone":
                icon = "🏆"
            elif m.type == "error":
                icon = "⚠️"
            
            content = m.content.replace('\n', ' ')[:100]
            if len(m.content) > 100:
                content += "..."
            
            lines.append(f"{i}. {icon} [{m.type}] {content}")
            
            # 添加来源
            if m.source:
                lines.append(f"   来源: {m.source}")
        
        return "\n".join(lines)
    
    def get_memory_for_prompt(self, user_message: str) -> str:
        """
        为LLM prompt获取相关记忆
        这是主入口函数
        """
        memories_text = self.load_relevant_memories(user_message)
        
        if memories_text:
            return f"\n{'='*50}\n相关上下文记忆（请考虑这些信息）：\n{'='*50}{memories_text}\n{'='*50}\n"
        
        return ""


# 便捷函数
def load_context_memory(user_message: str) -> str:
    """便捷函数：加载上下文记忆"""
    loader = ContextAwareMemoryLoader()
    return loader.get_memory_for_prompt(user_message)


if __name__ == "__main__":
    # 测试
    test_messages = [
        "优化记忆系统",
        "检查VM状态",
        "开始进化任务",
    ]
    
    for msg in test_messages:
        print(f"\n用户消息: {msg}")
        print("-" * 50)
        memory = load_context_memory(msg)
        if memory:
            print(memory)
        else:
            print("(无相关记忆)")
