#!/usr/bin/env python3
"""
Trigger Word Handler - 触发词处理模块
根据vestige的触发词设计，为森森集成关键词识别和自动响应

使用方式:
    from trigger_handler import TriggerHandler
    handler = TriggerHandler()
    result = handler.process_message("记住这个: Python最佳实践")
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
DATA_DIR = WORKSPACE / "data"


class TriggerAction(Enum):
    """触发动作类型"""
    SAVE_TO_LEARNING_DEBT = "save_to_learning_debt"
    MARK_HIGH_SIGNAL = "mark_high_signal"
    SAVE_USER_PREFERENCE = "save_user_preference"
    CREATE_TODO = "create_todo"
    CREATE_CRON_REMINDER = "create_cron_reminder"
    FORCE_MULTI_AGENT = "force_multi_agent"
    RECORD_IMPORTANT = "record_important"


class TriggerWordHandler:
    """触发词处理器"""
    
    # 触发词映射表 (基于vestige设计)
    TRIGGER_PATTERNS = {
        # 记忆相关
        r"记住[这那]?个[:\s]*(.+)": {
            "action": TriggerAction.SAVE_TO_LEARNING_DEBT,
            "priority": "normal",
            "signal_boost": 2,
            "description": "记录到学习债务"
        },
        r"(?:这|那)很?重要[:\s]*(.+)": {
            "action": TriggerAction.RECORD_IMPORTANT,
            "priority": "high",
            "signal_boost": 3,
            "description": "标记为高Signal重要内容"
        },
        r"我(?:总是|经常)\s*(.+)": {
            "action": TriggerAction.SAVE_USER_PREFERENCE,
            "priority": "normal",
            "category": "behavior_pattern",
            "description": "记录用户行为模式"
        },
        r"我(?:偏好|喜欢|倾向)\s*(.+)": {
            "action": TriggerAction.SAVE_USER_PREFERENCE,
            "priority": "normal",
            "category": "preference",
            "description": "记录用户偏好"
        },
        r"别忘了?\s*(.+)": {
            "action": TriggerAction.CREATE_TODO,
            "priority": "high",
            "description": "创建待办事项"
        },
        
        # 任务相关
        r"提醒[我]?\s*(?:在)?\s*(.+?)(?:时|时候)?[:\s]*(.+)": {
            "action": TriggerAction.CREATE_CRON_REMINDER,
            "priority": "normal",
            "description": "创建定时提醒"
        },
        r"稍后处理[:\s]*(.+)": {
            "action": TriggerAction.SAVE_TO_LEARNING_DEBT,
            "priority": "low",
            "signal_boost": 1,
            "description": "添加到学习债务(低优先级)"
        },
        
        # Multi-Agent (已存在)
        r"^多专家讨论[：:]\s*(.+)": {
            "action": TriggerAction.FORCE_MULTI_AGENT,
            "priority": "critical",
            "description": "强制启动Multi-Agent深度讨论"
        },
        
        #  vestige风格触发词
        r"(?:Don't forget|don'?t forget)\s*(.+)": {
            "action": TriggerAction.CREATE_TODO,
            "priority": "high",
            "description": "创建高优先级待办(英文)"
        },
        r"(?:I always|I never)\s*(.+)": {
            "action": TriggerAction.SAVE_USER_PREFERENCE,
            "priority": "normal",
            "category": "behavior_pattern",
            "description": "记录行为模式(英文)"
        },
        r"(?:I prefer|I like)\s*(.+)": {
            "action": TriggerAction.SAVE_USER_PREFERENCE,
            "priority": "normal",
            "category": "preference",
            "description": "记录偏好(英文)"
        },
        r"(?:Remind me)\s*(.+)": {
            "action": TriggerAction.CREATE_CRON_REMINDER,
            "priority": "normal",
            "description": "创建提醒(英文)"
        },
    }
    
    def __init__(self):
        self.trigger_log = DATA_DIR / "trigger-log.jsonl"
        self.trigger_log.parent.mkdir(exist_ok=True)
    
    def process_message(self, message: str) -> Optional[Dict]:
        """
        处理用户消息，检查是否包含触发词
        
        Returns:
            如果匹配到触发词，返回处理结果字典
            如果没有匹配，返回None
        """
        message = message.strip()
        
        for pattern, config in self.TRIGGER_PATTERNS.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                result = self._handle_trigger(match, config, message)
                self._log_trigger(result)
                return result
        
        return None
    
    def _handle_trigger(self, match: re.Match, config: Dict, original_message: str) -> Dict:
        """处理触发的动作"""
        action = config["action"]
        groups = match.groups()
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "original_message": original_message,
            "action": action.value,
            "priority": config.get("priority", "normal"),
            "description": config.get("description", ""),
            "matched_groups": groups,
            "executed": False,
            "result": None
        }
        
        # 执行对应动作
        if action == TriggerAction.SAVE_TO_LEARNING_DEBT:
            content = groups[0] if groups else original_message
            result["result"] = self._save_to_learning_debt(
                content, 
                config.get("signal_boost", 2),
                config.get("priority", "normal")
            )
            result["executed"] = True
            
        elif action == TriggerAction.RECORD_IMPORTANT:
            content = groups[0] if groups else original_message
            result["result"] = self._save_to_learning_debt(
                content,
                config.get("signal_boost", 3),
                "high"
            )
            result["executed"] = True
            
        elif action == TriggerAction.SAVE_USER_PREFERENCE:
            preference = groups[0] if groups else ""
            category = config.get("category", "preference")
            result["result"] = self._save_user_preference(preference, category)
            result["executed"] = True
            
        elif action == TriggerAction.CREATE_TODO:
            task = groups[0] if groups else original_message
            result["result"] = self._create_todo(task, config.get("priority", "normal"))
            result["executed"] = True
            
        elif action == TriggerAction.CREATE_CRON_REMINDER:
            # 解析时间表达式
            time_expr = groups[0] if len(groups) > 0 else ""
            task = groups[1] if len(groups) > 1 else time_expr
            result["result"] = self._create_reminder(time_expr, task)
            result["executed"] = True
            
        elif action == TriggerAction.FORCE_MULTI_AGENT:
            topic = groups[0] if groups else original_message
            result["result"] = {
                "action": "FORCE_MULTI_AGENT",
                "topic": topic,
                "note": "此动作由主会话处理"
            }
            result["executed"] = True
        
        return result
    
    def _save_to_learning_debt(self, content: str, signal_boost: int, priority: str) -> Dict:
        """保存到学习债务"""
        debt_file = MEMORY_DIR / "learning-debt.md"
        
        entry = f"\n- ⏳ **{content[:50]}**... (Signal {5 + signal_boost}/10, {priority} priority)\n"
        entry += f"  - 触发时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        entry += f"  - 来源: 触发词自动记录\n"
        
        try:
            if debt_file.exists():
                with open(debt_file, "a", encoding="utf-8") as f:
                    f.write(entry)
            else:
                with open(debt_file, "w", encoding="utf-8") as f:
                    f.write("# 学习债务\n\n" + entry)
            
            return {
                "status": "success",
                "file": str(debt_file),
                "content_preview": content[:100],
                "signal": 5 + signal_boost
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _save_user_preference(self, preference: str, category: str) -> Dict:
        """保存用户偏好到USER.md"""
        user_file = WORKSPACE / "USER.md"
        
        entry = f"\n- **{category}**: {preference}"
        entry += f" (记录于: {datetime.now().strftime('%Y-%m-%d')})\n"
        
        try:
            if user_file.exists():
                with open(user_file, "a", encoding="utf-8") as f:
                    f.write(entry)
            
            return {
                "status": "success",
                "file": str(user_file),
                "category": category,
                "preference": preference
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _create_todo(self, task: str, priority: str) -> Dict:
        """创建待办事项"""
        todo_file = MEMORY_DIR / "active-tasks.md"
        
        priority_emoji = {"high": "🔴", "normal": "🟡", "low": "🟢"}.get(priority, "🟡")
        entry = f"\n- {priority_emoji} {task}"
        entry += f" (创建于: {datetime.now().strftime('%Y-%m-%d %H:%M')})\n"
        
        try:
            if todo_file.exists():
                with open(todo_file, "a", encoding="utf-8") as f:
                    f.write(entry)
            else:
                with open(todo_file, "w", encoding="utf-8") as f:
                    f.write("# 待办事项\n\n" + entry)
            
            return {
                "status": "success",
                "file": str(todo_file),
                "task": task,
                "priority": priority
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _create_reminder(self, time_expr: str, task: str) -> Dict:
        """创建定时提醒 (简化版，实际需要cron配置)"""
        reminder = {
            "time_expression": time_expr,
            "task": task,
            "created_at": datetime.now().isoformat(),
            "note": "需要手动配置cron任务"
        }
        
        # 保存到提醒列表
        reminder_file = DATA_DIR / "pending-reminders.json"
        try:
            reminders = []
            if reminder_file.exists():
                with open(reminder_file, "r", encoding="utf-8") as f:
                    reminders = json.load(f)
            
            reminders.append(reminder)
            
            with open(reminder_file, "w", encoding="utf-8") as f:
                json.dump(reminders, f, indent=2, ensure_ascii=False)
            
            return {
                "status": "success",
                "file": str(reminder_file),
                "reminder": reminder
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _log_trigger(self, result: Dict):
        """记录触发日志"""
        try:
            with open(self.trigger_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"触发日志记录失败: {e}")
    
    def get_trigger_stats(self) -> Dict:
        """获取触发统计信息"""
        if not self.trigger_log.exists():
            return {"total_triggers": 0}
        
        try:
            with open(self.trigger_log, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            actions = {}
            for line in lines:
                try:
                    record = json.loads(line)
                    action = record.get("action", "unknown")
                    actions[action] = actions.get(action, 0) + 1
                except:
                    continue
            
            return {
                "total_triggers": len(lines),
                "action_distribution": actions
            }
        except Exception as e:
            return {"error": str(e)}


# 便捷函数
def check_triggers(message: str) -> Optional[Dict]:
    """快速检查消息中的触发词"""
    handler = TriggerWordHandler()
    return handler.process_message(message)


if __name__ == "__main__":
    # 测试
    test_messages = [
        "记住这个: Python最佳实践",
        "这很重要: 需要深入学习MCP协议",
        "我总是使用Git进行版本控制",
        "我偏好使用VS Code编辑器",
        "别忘了处理那个bug",
        "提醒我明天下午3点: 开会",
        "多专家讨论: 这个架构设计是否可行？",
        "这是一个普通消息，没有触发词"
    ]
    
    handler = TriggerWordHandler()
    
    print("=== 触发词测试 ===\n")
    for msg in test_messages:
        result = handler.process_message(msg)
        if result:
            print(f"✅ 触发: {msg[:40]}...")
            print(f"   动作: {result['description']}")
            print(f"   优先级: {result['priority']}")
            print()
        else:
            print(f"❌ 未触发: {msg[:40]}...")
    
    print("\n=== 统计 ===")
    stats = handler.get_trigger_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
