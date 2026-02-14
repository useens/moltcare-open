#!/usr/bin/env python3
"""
双节点通信管理器
防止永久静默，智能触发对话
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

class CommunicationManager:
    """通信管理器 - 智能控制对话触发"""
    
    def __init__(self):
        self.memory_dir = Path("/root/.openclaw/workspace/memory")
        self.state_file = self.memory_dir / "communication-state.json"
        
        # 配置
        self.heartbeat_interval = 1800  # 30分钟纯数据心跳
        self.silence_threshold = 5400   # 90分钟无AI对话触发检查
        self.max_silence = 10800        # 3小时强制AI对话
        
        # 状态
        self.last_ai_interaction = self._load_state().get("last_ai_interaction", datetime.now().isoformat())
        self.last_heartbeat = datetime.now()
        self.conversation_count = 0
        
    def _load_state(self) -> dict:
        """加载状态"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                return {}
        return {}
    
    def _save_state(self):
        """保存状态"""
        self.state_file.write_text(json.dumps({
            "last_ai_interaction": self.last_ai_interaction,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "conversation_count": self.conversation_count,
            "updated_at": datetime.now().isoformat()
        }, indent=2))
    
    def get_silence_duration(self) -> float:
        """获取静默时长（秒）"""
        last_ai = datetime.fromisoformat(self.last_ai_interaction)
        return (datetime.now() - last_ai).total_seconds()
    
    def should_trigger_ai_dialogue(self) -> tuple:
        """
        判断是否应触发AI对话
        返回: (should_trigger, reason)
        """
        silence = self.get_silence_duration()
        
        # 检查点1: 90分钟静默 - 发送问候
        if silence > self.silence_threshold and silence < self.max_silence:
            return (True, "silence_check_90min")
        
        # 检查点2: 3小时静默 - 强制AI对话
        if silence >= self.max_silence:
            return (True, "forced_dialogue_3h")
        
        return (False, "normal_operation")
    
    def record_ai_interaction(self):
        """记录AI交互"""
        self.last_ai_interaction = datetime.now().isoformat()
        self.conversation_count += 1
        self._save_state()
    
    def get_conversation_suggestions(self) -> list:
        """获取对话建议主题"""
        suggestions = []
        
        # 基于时间触发
        hour = datetime.now().hour
        if hour == 9:
            suggestions.append("晨会: 今日任务规划")
        elif hour == 18:
            suggestions.append("复盘: 今日执行总结")
        elif hour == 23:
            suggestions.append("交接: 夜间任务准备")
        
        # 基于系统状态
        # 这里可以读取health check结果
        suggestions.append("系统健康检查反馈")
        
        # 基于学习债务
        # 这里可以检查memory/learning-debt.md
        suggestions.append("学习债务处理讨论")
        
        return suggestions
    
    def generate_silence_breaker(self) -> str:
        """生成打破静默的消息"""
        silence_hours = self.get_silence_duration() / 3600
        suggestions = self.get_conversation_suggestions()
        
        if suggestions:
            topic = suggestions[0]
            return f"🌲 静默检测: 已超过{silence_hours:.1f}小时无深度交流。建议主题: {topic}"
        else:
            return f"🌲 静默检测: 已超过{silence_hours:.1f}小时。一切正常吗？"

# 静默检测触发器配置
SILENCE_TRIGGERS = {
    "90min_check": {
        "description": "90分钟静默检查",
        "action": "发送问候消息（模板化，低token）",
        "ai_generate": False
    },
    "3h_forced": {
        "description": "3小时强制对话",
        "action": "AI生成状态检查对话",
        "ai_generate": True,
        "priority": "high"
    },
    "6h_emergency": {
        "description": "6小时紧急告警",
        "action": "立即AI对话+用户告警",
        "ai_generate": True,
        "priority": "critical",
        "notify_user": True
    }
}

# 对话触发条件（白名单）
DIALOGUE_TRIGGERS = {
    # 必须AI对话
    "user_explicit_request": "用户明确要求",
    "new_problem_encountered": "遇到新问题",
    "decision_required": "需要决策判断",
    "system_anomaly": "系统异常",
    "silence_3h": "3小时静默",
    "scheduled_sync": "定时同步（每6小时）",
    
    # 禁止AI对话（用模板或数据）
    "heartbeat": "心跳检查",
    "status_report": "状态汇报",
    "task_progress": "进度更新",
    "data_sync": "数据同步",
    "acknowledgment": "确认收到",
}

if __name__ == "__main__":
    # 测试
    manager = CommunicationManager()
    
    print("通信管理器测试")
    print(f"静默时长: {manager.get_silence_duration()/60:.1f} 分钟")
    
    should_trigger, reason = manager.should_trigger_ai_dialogue()
    print(f"应触发对话: {should_trigger}, 原因: {reason}")
    
    if should_trigger:
        print(f"建议消息: {manager.generate_silence_breaker()}")
    
    print(f"\n对话建议: {manager.get_conversation_suggestions()}")
