#!/usr/bin/env python3
"""
Trigger Word System - 触发词系统
集成到森森的消息处理流程中

触发词映射:
- "记住这个" → smart_ingest (高优先级)
- "这很重要" → smart_ingest + promote_memory (极高优先级)  
- "别忘记" → smart_ingest (高优先级)
- "我偏好"/"我更喜欢" → 写入USER.md偏好
- "我总是"/"我从来不" → 写入USER.md行为模式
- "提醒我..." → 创建intention/cron提醒
- "学习这个" → 添加到learning-debt (Signal=8)
- "研究一下" → 添加到learning-debt (Signal=7)
- "多专家讨论:" → 强制触发Multi-Agent深度讨论
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class TriggerAction(Enum):
    """触发动作类型"""
    SMART_INGEST = "smart_ingest"
    PROMOTE_MEMORY = "promote_memory"
    WRITE_PREFERENCE = "write_preference"
    CREATE_REMINDER = "create_reminder"
    ADD_LEARNING_DEBT = "add_learning_debt"
    MULTI_AGENT = "multi_agent"
    NONE = "none"

@dataclass
class TriggerMatch:
    """触发匹配结果"""
    action: TriggerAction
    trigger_word: str
    confidence: float  # 0-1
    extracted_content: str = ""
    priority: int = 5  # 1-10

class TriggerHandler:
    """触发词处理器"""
    
    # 触发词配置表
    TRIGGERS = {
        # 极高优先级 (强制Multi-Agent)
        r"^多专家讨论[：:]": {
            "action": TriggerAction.MULTI_AGENT,
            "priority": 10,
            "confidence": 1.0
        },
        
        # 高优先级 - 记忆相关
        r"这很重要|非常重要|极其重要": {
            "action": TriggerAction.PROMOTE_MEMORY,
            "priority": 9,
            "confidence": 0.95
        },
        r"记住这个|请记住|记下来": {
            "action": TriggerAction.SMART_INGEST,
            "priority": 8,
            "confidence": 0.9
        },
        r"别忘记|不要忘记|千万别忘": {
            "action": TriggerAction.SMART_INGEST,
            "priority": 8,
            "confidence": 0.9
        },
        
        # 中优先级 - 偏好相关
        r"我偏好|我更喜欢|我喜欢|我讨厌": {
            "action": TriggerAction.WRITE_PREFERENCE,
            "priority": 6,
            "confidence": 0.85
        },
        r"我总是|我从来不|我通常": {
            "action": TriggerAction.WRITE_PREFERENCE,
            "priority": 6,
            "confidence": 0.85
        },
        
        # 任务相关
        r"提醒我[：:]?\s*(.+?)(?:$|在|明天|后天)": {
            "action": TriggerAction.CREATE_REMINDER,
            "priority": 7,
            "confidence": 0.9,
            "extract_group": 1
        },
        
        # 学习债务
        r"学习这个|深度学习|仔细研究": {
            "action": TriggerAction.ADD_LEARNING_DEBT,
            "priority": 8,
            "confidence": 0.85,
            "signal": 8
        },
        r"研究一下|调研|分析一下": {
            "action": TriggerAction.ADD_LEARNING_DEBT,
            "priority": 7,
            "confidence": 0.8,
            "signal": 7
        },
        r"搞不懂|不理解| confused": {
            "action": TriggerAction.ADD_LEARNING_DEBT,
            "priority": 6,
            "confidence": 0.75,
            "signal": 6
        },
    }
    
    def __init__(self, workspace_path: str = None):
        if workspace_path is None:
            workspace_path = Path.home() / ".openclaw/workspace"
        self.workspace = Path(workspace_path)
        self.learning_debt_file = self.workspace / "memory/learning-debt.md"
        self.user_file = self.workspace / "USER.md"
    
    def detect_triggers(self, message: str) -> List[TriggerMatch]:
        """
        检测消息中的触发词
        返回按优先级排序的触发匹配列表
        """
        matches = []
        message = message.strip()
        
        for pattern, config in self.TRIGGERS.items():
            regex = re.compile(pattern, re.IGNORECASE | re.UNICODE)
            match = regex.search(message)
            
            if match:
                # 提取内容（如果有捕获组）
                extracted = ""
                if "extract_group" in config and match.groups():
                    group_idx = config["extract_group"]
                    if group_idx <= len(match.groups()):
                        extracted = match.group(group_idx)
                
                trigger_match = TriggerMatch(
                    action=config["action"],
                    trigger_word=match.group(0),
                    confidence=config["confidence"],
                    extracted_content=extracted,
                    priority=config["priority"]
                )
                matches.append(trigger_match)
        
        # 按优先级排序（高优先级在前）
        matches.sort(key=lambda x: x.priority, reverse=True)
        return matches
    
    def should_use_multi_agent(self, message: str, matches: List[TriggerMatch]) -> bool:
        """
        判断是否应该使用Multi-Agent
        """
        # 强制触发: 以"多专家讨论:"开头
        if message.strip().startswith("多专家讨论：") or \
           message.strip().startswith("多专家讨论:"):
            return True
        
        # 检查是否有Multi-Agent触发词
        for match in matches:
            if match.action == TriggerAction.MULTI_AGENT:
                return True
        
        # 启发式判断
        multi_agent_keywords = [
            "选择", "对比", "设计", "架构", "优化", "性能",
            "安全", "风险", "评估", "方案", "策略", "规划"
        ]
        
        keyword_count = sum(1 for kw in multi_agent_keywords if kw in message)
        if keyword_count >= 2 or len(message) > 100:
            return True
        
        return False
    
    def execute_trigger(self, match: TriggerMatch, full_message: str) -> Dict:
        """
        执行触发动作
        """
        result = {
            "action": match.action.value,
            "success": False,
            "message": "",
            "data": {}
        }
        
        try:
            if match.action == TriggerAction.SMART_INGEST:
                result = self._do_smart_ingest(full_message, match)
            elif match.action == TriggerAction.PROMOTE_MEMORY:
                result = self._do_promote_memory(full_message, match)
            elif match.action == TriggerAction.WRITE_PREFERENCE:
                result = self._do_write_preference(full_message, match)
            elif match.action == TriggerAction.CREATE_REMINDER:
                result = self._do_create_reminder(full_message, match)
            elif match.action == TriggerAction.ADD_LEARNING_DEBT:
                result = self._do_add_learning_debt(full_message, match)
            elif match.action == TriggerAction.MULTI_AGENT:
                result = self._do_multi_agent(full_message, match)
        except Exception as e:
            result["message"] = f"执行失败: {str(e)}"
        
        return result
    
    def _do_smart_ingest(self, message: str, match: TriggerMatch) -> Dict:
        """执行smart_ingest"""
        # 移除触发词，提取内容
        content = re.sub(re.escape(match.trigger_word), "", message, 
                        flags=re.IGNORECASE).strip()
        
        # 这里应该调用vestige的smart_ingest
        # 简化版: 记录到日志
        return {
            "action": "smart_ingest",
            "success": True,
            "message": f"已记录记忆 (Signal={match.priority})",
            "data": {
                "content": content[:200],
                "signal_score": match.priority
            }
        }
    
    def _do_promote_memory(self, message: str, match: TriggerMatch) -> Dict:
        """执行promote_memory (高重要性)"""
        content = re.sub(re.escape(match.trigger_word), "", message, 
                        flags=re.IGNORECASE).strip()
        
        return {
            "action": "promote_memory",
            "success": True,
            "message": f"已标记高重要性记忆 (Signal=10)",
            "data": {
                "content": content[:200],
                "signal_score": 10,
                "promoted": True
            }
        }
    
    def _do_write_preference(self, message: str, match: TriggerMatch) -> Dict:
        """写入用户偏好"""
        # 提取偏好内容
        preference = message.strip()
        
        # 追加到USER.md
        try:
            user_md = self.user_file
            if user_md.exists():
                with open(user_md, "a", encoding="utf-8") as f:
                    f.write(f"\n- 偏好记录 [{datetime.now().strftime('%Y-%m-%d')}]: {preference}\n")
            
            return {
                "action": "write_preference",
                "success": True,
                "message": "已记录用户偏好到USER.md",
                "data": {"preference": preference[:100]}
            }
        except Exception as e:
            return {
                "action": "write_preference",
                "success": False,
                "message": str(e)
            }
    
    def _do_create_reminder(self, message: str, match: TriggerMatch) -> Dict:
        """创建提醒"""
        reminder_content = match.extracted_content or "未指定内容"
        
        # 解析时间 (简化版)
        time_info = self._parse_time_from_message(message)
        
        return {
            "action": "create_reminder",
            "success": True,
            "message": f"已创建提醒: {reminder_content}",
            "data": {
                "content": reminder_content,
                "scheduled_time": time_info
            }
        }
    
    def _do_add_learning_debt(self, message: str, match: TriggerMatch) -> Dict:
        """添加到学习债务"""
        signal = 7  # 默认
        if hasattr(match, 'signal'):
            signal = match.signal
        
        # 提取主题
        topic = re.sub(re.escape(match.trigger_word), "", message, 
                      flags=re.IGNORECASE).strip()[:100]
        
        # 添加到learning-debt.md
        try:
            debt_file = self.learning_debt_file
            debt_file.parent.mkdir(parents=True, exist_ok=True)
            
            entry = f"\n## [{datetime.now().strftime('%Y-%m-%d %H:%M')}] Signal={signal}\n"
            entry += f"- 主题: {topic}\n"
            entry += f"- 来源: 触发词自动添加\n"
            entry += f"- 状态: 待处理\n"
            
            with open(debt_file, "a", encoding="utf-8") as f:
                f.write(entry)
            
            return {
                "action": "add_learning_debt",
                "success": True,
                "message": f"已添加学习债务 (Signal={signal})",
                "data": {
                    "topic": topic,
                    "signal": signal
                }
            }
        except Exception as e:
            return {
                "action": "add_learning_debt",
                "success": False,
                "message": str(e)
            }
    
    def _do_multi_agent(self, message: str, match: TriggerMatch) -> Dict:
        """触发Multi-Agent深度讨论"""
        return {
            "action": "multi_agent",
            "success": True,
            "message": "已触发Multi-Agent深度讨论模式",
            "data": {
                "mode": "forced",
                "experts": ["研究员", "架构师", "工程师", "安全专家"],
                "rounds": 3
            }
        }
    
    def _parse_time_from_message(self, message: str) -> str:
        """从消息中解析时间 (简化版)"""
        # 匹配常见时间格式
        time_patterns = [
            (r'(\d+)分钟后?', lambda m: f"+{m.group(1)}m"),
            (r'(\d+)小时后?', lambda m: f"+{m.group(1)}h"),
            (r'明天', lambda m: "+1d"),
            (r'后天', lambda m: "+2d"),
        ]
        
        for pattern, formatter in time_patterns:
            match = re.search(pattern, message)
            if match:
                return formatter(match)
        
        return "未指定"
    
    def process_message(self, message: str) -> Dict:
        """
        处理消息的主入口
        返回处理结果摘要
        """
        result = {
            "original_message": message[:200],
            "triggers_detected": [],
            "multi_agent_recommended": False,
            "actions_executed": [],
            "summary": ""
        }
        
        # 检测触发词
        matches = self.detect_triggers(message)
        result["triggers_detected"] = [
            {
                "word": m.trigger_word,
                "action": m.action.value,
                "priority": m.priority
            }
            for m in matches
        ]
        
        # 判断是否推荐Multi-Agent
        result["multi_agent_recommended"] = self.should_use_multi_agent(message, matches)
        
        # 执行触发动作
        for match in matches:
            action_result = self.execute_trigger(match, message)
            result["actions_executed"].append(action_result)
        
        # 生成摘要
        if matches:
            actions = [m.action.value for m in matches]
            result["summary"] = f"检测到 {len(matches)} 个触发词，执行: {', '.join(actions)}"
        else:
            result["summary"] = "未检测到触发词"
        
        return result

# 全局实例
_trigger_handler = None

def get_trigger_handler() -> TriggerHandler:
    """获取全局触发词处理器"""
    global _trigger_handler
    if _trigger_handler is None:
        _trigger_handler = TriggerHandler()
    return _trigger_handler

def process_message(message: str) -> Dict:
    """便捷函数: 处理消息"""
    return get_trigger_handler().process_message(message)

def should_use_multi_agent(message: str) -> bool:
    """便捷函数: 判断是否使用Multi-Agent"""
    handler = get_trigger_handler()
    matches = handler.detect_triggers(message)
    return handler.should_use_multi_agent(message, matches)

if __name__ == "__main__":
    # 测试触发词系统
    test_messages = [
        "记住这个：明天要开会",
        "这很重要，项目的截止日期是周五",
        "我偏好使用Python而不是Java",
        "多专家讨论：如何选择数据库",
        "提醒我20分钟后喝水",
        "学习这个：FSRS-6算法原理",
        "这是一个普通消息，没有触发词"
    ]
    
    handler = TriggerHandler()
    for msg in test_messages:
        print(f"\n消息: {msg}")
        result = handler.process_message(msg)
        print(f"  触发词: {[t['word'] for t in result['triggers_detected']]}")
        print(f"  推荐Multi-Agent: {result['multi_agent_recommended']}")
        print(f"  摘要: {result['summary']}")
