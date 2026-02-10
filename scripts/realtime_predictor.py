#!/usr/bin/env python3
"""
林林v5.0 实时预判触发器 (Real-time Predictor)
版本: v5.0
职责: 实时监控用户活动，触发预判引擎

核心功能:
1. 对话后实时分析
2. 定时触发预测
3. 上下文变化检测
4. 用户活跃状态监控
5. 事件驱动触发
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prediction_integration import (
    PredictionIntegration, PredictionResult, PredictionTriggerType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("realtime_predictor")


class TriggerEvent(Enum):
    """触发事件类型"""
    CONVERSATION_END = "conversation_end"
    SCHEDULED_CHECK = "scheduled_check"
    CONTEXT_UPDATE = "context_update"
    USER_ACTIVE = "user_active"
    CALENDAR_EVENT = "calendar_event"
    EMAIL_ARRIVAL = "email_arrival"
    PROJECT_UPDATE = "project_update"


@dataclass
class TriggerContext:
    """触发上下文"""
    event_type: TriggerEvent
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    user_id: str = "default"


class RealtimePredictor:
    """
    实时预判触发器
    负责监听各种事件并触发预测
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.prediction_integration = PredictionIntegration(data_dir)
        
        # 触发器配置
        self.scheduled_interval_minutes = 30  # 定时检查间隔
        self.context_check_interval_minutes = 5  # 上下文检查间隔
        self.min_confidence_for_proactive = 0.75  # 主动建议最小置信度
        
        # 状态
        self.running = False
        self.last_conversation_time: Optional[datetime] = None
        self.last_context_hash: Optional[str] = None
        self.conversation_history: List[Dict] = []
        self.max_history = 50
        
        # 回调函数
        self.on_suggestion: Optional[Callable[[List[PredictionResult]], None]] = None
        self.on_trigger: Optional[Callable[[TriggerEvent, List[PredictionResult]], None]] = None
        
        # 上下文缓存
        self.context_cache: Dict[str, Any] = {}
        
        # 任务引用
        self._tasks: List[asyncio.Task] = []
    
    def set_callbacks(self,
                     on_suggestion: Optional[Callable[[List[PredictionResult]], None]] = None,
                     on_trigger: Optional[Callable[[TriggerEvent, List[PredictionResult]], None]] = None):
        """设置回调函数"""
        self.on_suggestion = on_suggestion
        self.on_trigger = on_trigger
        
        # 同时设置集成模块的回调
        self.prediction_integration.set_callbacks(
            on_prediction=None,
            on_suggestion=on_suggestion
        )
    
    async def start(self):
        """启动实时预判器"""
        if self.running:
            return
        
        self.running = True
        logger.info("[实时预判器] 启动")
        
        # 启动定时任务
        self._tasks = [
            asyncio.create_task(self._scheduled_check_loop()),
            asyncio.create_task(self._context_monitor_loop()),
        ]
    
    async def stop(self):
        """停止实时预判器"""
        self.running = False
        logger.info("[实时预判器] 停止")
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
    
    # ========== 1. 实时对话分析 ==========
    
    async def on_conversation_end(self, conversation: Dict, 
                                  context: Optional[Dict] = None) -> List[PredictionResult]:
        """
        对话结束时调用
        分析对话内容并生成预测
        """
        logger.info("[实时预判器] 对话结束，开始分析...")
        
        # 记录对话历史
        self.conversation_history.append(conversation)
        self.conversation_history = self.conversation_history[-self.max_history:]
        self.last_conversation_time = datetime.now()
        
        # 合并上下文
        full_context = self._merge_context(context)
        full_context["conversation_history"] = self.conversation_history[-5:]  # 最近5条
        
        # 调用预判引擎分析
        predictions = await self.prediction_integration.analyze_conversation(
            conversation, full_context
        )
        
        # 触发回调
        trigger_context = TriggerContext(
            event_type=TriggerEvent.CONVERSATION_END,
            timestamp=datetime.now(),
            data={"conversation": conversation}
        )
        
        await self._handle_predictions(trigger_context, predictions)
        
        return predictions
    
    # ========== 2. 定时触发 ==========
    
    async def _scheduled_check_loop(self):
        """定时检查循环"""
        while self.running:
            try:
                await asyncio.sleep(self.scheduled_interval_minutes * 60)
                
                if not self.running:
                    break
                
                logger.info("[实时预判器] 执行定时检查...")
                
                # 获取当前上下文
                context = await self._fetch_current_context()
                
                # 生成预测
                predictions = await self.prediction_integration.generate_proactive_suggestions(context)
                
                # 触发回调
                trigger_context = TriggerContext(
                    event_type=TriggerEvent.SCHEDULED_CHECK,
                    timestamp=datetime.now(),
                    data={"interval_minutes": self.scheduled_interval_minutes}
                )
                
                await self._handle_predictions(trigger_context, predictions)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[实时预判器] 定时检查错误: {e}")
    
    async def run_scheduled_check(self) -> List[PredictionResult]:
        """手动执行定时检查"""
        context = await self._fetch_current_context()
        predictions = await self.prediction_integration.generate_proactive_suggestions(context)
        
        trigger_context = TriggerContext(
            event_type=TriggerEvent.SCHEDULED_CHECK,
            timestamp=datetime.now(),
            data={"manual": True}
        )
        
        await self._handle_predictions(trigger_context, predictions)
        return predictions
    
    # ========== 3. 上下文变化检测 ==========
    
    async def _context_monitor_loop(self):
        """上下文监控循环"""
        while self.running:
            try:
                await asyncio.sleep(self.context_check_interval_minutes * 60)
                
                if not self.running:
                    break
                
                # 检查上下文变化
                has_changed, change_info = await self._check_context_changes()
                
                if has_changed:
                    logger.info(f"[实时预判器] 检测到上下文变化: {change_info}")
                    
                    context = await self._fetch_current_context()
                    predictions = await self.prediction_integration.generate_proactive_suggestions(context)
                    
                    trigger_context = TriggerContext(
                        event_type=TriggerEvent.CONTEXT_UPDATE,
                        timestamp=datetime.now(),
                        data={"changes": change_info}
                    )
                    
                    await self._handle_predictions(trigger_context, predictions)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[实时预判器] 上下文监控错误: {e}")
    
    async def _check_context_changes(self) -> tuple[bool, Dict]:
        """检查上下文是否发生变化"""
        changes = {}
        has_changed = False
        
        # 检查邮件变化
        try:
            current_emails = await self._fetch_emails()
            email_hash = self._hash_context(current_emails)
            
            if self.context_cache.get("email_hash") != email_hash:
                changes["emails"] = {"new_count": len(current_emails)}
                self.context_cache["email_hash"] = email_hash
                self.context_cache["emails"] = current_emails
                has_changed = True
        except Exception as e:
            logger.debug(f"检查邮件变化失败: {e}")
        
        # 检查日历变化
        try:
            current_calendar = await self._fetch_calendar()
            calendar_hash = self._hash_context(current_calendar)
            
            if self.context_cache.get("calendar_hash") != calendar_hash:
                changes["calendar"] = {"event_count": len(current_calendar)}
                self.context_cache["calendar_hash"] = calendar_hash
                self.context_cache["calendar"] = current_calendar
                has_changed = True
        except Exception as e:
            logger.debug(f"检查日历变化失败: {e}")
        
        return has_changed, changes
    
    def _hash_context(self, data: Any) -> str:
        """生成上下文哈希"""
        import hashlib
        return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    
    # ========== 4. 事件驱动触发 ==========
    
    async def on_calendar_event(self, event: Dict) -> List[PredictionResult]:
        """日历事件触发"""
        logger.info(f"[实时预判器] 日历事件触发: {event.get('title', '')}")
        
        context = await self._fetch_current_context()
        context["calendar"] = [event]
        
        predictions = await self.prediction_integration.generate_proactive_suggestions(context)
        
        trigger_context = TriggerContext(
            event_type=TriggerEvent.CALENDAR_EVENT,
            timestamp=datetime.now(),
            data={"event": event}
        )
        
        await self._handle_predictions(trigger_context, predictions)
        return predictions
    
    async def on_email_arrival(self, emails: List[Dict]) -> List[PredictionResult]:
        """新邮件到达触发"""
        unread_count = sum(1 for e in emails if e.get("unread", False))
        logger.info(f"[实时预判器] 新邮件到达: {len(emails)} 封, {unread_count} 封未读")
        
        context = await self._fetch_current_context()
        context["emails"] = emails
        
        predictions = await self.prediction_integration.generate_proactive_suggestions(context)
        
        trigger_context = TriggerContext(
            event_type=TriggerEvent.EMAIL_ARRIVAL,
            timestamp=datetime.now(),
            data={"email_count": len(emails), "unread_count": unread_count}
        )
        
        await self._handle_predictions(trigger_context, predictions)
        return predictions
    
    async def on_project_update(self, project: Dict) -> List[PredictionResult]:
        """项目更新触发"""
        logger.info(f"[实时预判器] 项目更新: {project.get('name', '')}")
        
        context = await self._fetch_current_context()
        context["projects"] = [project]
        
        predictions = await self.prediction_integration.generate_proactive_suggestions(context)
        
        trigger_context = TriggerContext(
            event_type=TriggerEvent.PROJECT_UPDATE,
            timestamp=datetime.now(),
            data={"project": project}
        )
        
        await self._handle_predictions(trigger_context, predictions)
        return predictions
    
    # ========== 辅助方法 ==========
    
    async def _handle_predictions(self, trigger_context: TriggerContext, 
                                  predictions: List[PredictionResult]):
        """处理预测结果"""
        # 过滤高置信度预测
        high_confidence = [p for p in predictions 
                         if p.confidence >= self.min_confidence_for_proactive]
        
        if high_confidence:
            logger.info(f"[实时预判器] 触发 {len(high_confidence)} 个高置信度预测")
            
            # 触发回调
            if self.on_trigger:
                try:
                    self.on_trigger(trigger_context.event_type, high_confidence)
                except Exception as e:
                    logger.error(f"触发回调失败: {e}")
            
            if self.on_suggestion:
                try:
                    self.on_suggestion(high_confidence)
                except Exception as e:
                    logger.error(f"建议回调失败: {e}")
    
    def _merge_context(self, context: Optional[Dict]) -> Dict:
        """合并上下文"""
        merged = self.context_cache.copy()
        if context:
            merged.update(context)
        return merged
    
    async def _fetch_current_context(self) -> Dict:
        """获取当前上下文"""
        context = {}
        
        # 获取邮件
        try:
            context["emails"] = await self._fetch_emails()
        except Exception as e:
            logger.debug(f"获取邮件失败: {e}")
        
        # 获取日历
        try:
            context["calendar"] = await self._fetch_calendar()
        except Exception as e:
            logger.debug(f"获取日历失败: {e}")
        
        # 获取项目
        try:
            context["projects"] = await self._fetch_projects()
        except Exception as e:
            logger.debug(f"获取项目失败: {e}")
        
        return context
    
    async def _fetch_emails(self) -> List[Dict]:
        """获取邮件数据（可扩展为实际API调用）"""
        # 从缓存获取
        if "emails" in self.context_cache:
            return self.context_cache["emails"]
        return []
    
    async def _fetch_calendar(self) -> List[Dict]:
        """获取日历数据（可扩展为实际API调用）"""
        # 从缓存获取
        if "calendar" in self.context_cache:
            return self.context_cache["calendar"]
        return []
    
    async def _fetch_projects(self) -> List[Dict]:
        """获取项目数据（可扩展为实际API调用）"""
        # 从缓存获取
        if "projects" in self.context_cache:
            return self.context_cache["projects"]
        return []
    
    # ========== 反馈记录 ==========
    
    def record_feedback(self, prediction_id: str, was_accurate: bool,
                       actual_need: Optional[str] = None, was_accepted: bool = False):
        """记录用户反馈"""
        self.prediction_integration.record_feedback(
            prediction_id, was_accurate, actual_need, was_accepted
        )
    
    # ========== 配置管理 ==========
    
    def update_config(self, **kwargs):
        """更新配置"""
        if "scheduled_interval_minutes" in kwargs:
            self.scheduled_interval_minutes = kwargs["scheduled_interval_minutes"]
        if "context_check_interval_minutes" in kwargs:
            self.context_check_interval_minutes = kwargs["context_check_interval_minutes"]
        if "min_confidence_for_proactive" in kwargs:
            self.min_confidence_for_proactive = kwargs["min_confidence_for_proactive"]
        
        logger.info(f"[实时预判器] 配置已更新: {kwargs}")
    
    def get_config(self) -> Dict:
        """获取当前配置"""
        return {
            "scheduled_interval_minutes": self.scheduled_interval_minutes,
            "context_check_interval_minutes": self.context_check_interval_minutes,
            "min_confidence_for_proactive": self.min_confidence_for_proactive,
            "running": self.running,
            "last_conversation_time": self.last_conversation_time.isoformat() if self.last_conversation_time else None
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "conversation_history_count": len(self.conversation_history),
            "last_conversation_time": self.last_conversation_time.isoformat() if self.last_conversation_time else None,
            "running": self.running,
            "prediction_report": self.prediction_integration.get_prediction_report()
        }


# ========== 主流程集成装饰器 ==========

class PredictionDecorators:
    """预判引擎装饰器集合"""
    
    @staticmethod
    def with_post_conversation_prediction(predictor: RealtimePredictor):
        """对话后预测装饰器"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # 执行原始函数
                result = await func(*args, **kwargs)
                
                # 触发预测
                conversation = kwargs.get("conversation") or (args[0] if args else None)
                if conversation:
                    await predictor.on_conversation_end(conversation)
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def with_context_update_prediction(predictor: RealtimePredictor, context_type: str):
        """上下文更新预测装饰器"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # 执行原始函数
                result = await func(*args, **kwargs)
                
                # 根据类型触发
                if context_type == "email":
                    emails = result if isinstance(result, list) else []
                    if emails:
                        await predictor.on_email_arrival(emails)
                elif context_type == "calendar":
                    event = result if isinstance(result, dict) else None
                    if event:
                        await predictor.on_calendar_event(event)
                elif context_type == "project":
                    project = result if isinstance(result, dict) else None
                    if project:
                        await predictor.on_project_update(project)
                
                return result
            return wrapper
        return decorator


# ========== 便捷函数 ==========

_global_predictor: Optional[RealtimePredictor] = None


def get_predictor(data_dir: str = "data") -> RealtimePredictor:
    """获取全局预判器实例"""
    global _global_predictor
    if _global_predictor is None:
        _global_predictor = RealtimePredictor(data_dir)
    return _global_predictor


async def start_prediction_service(data_dir: str = "data") -> RealtimePredictor:
    """启动预判服务"""
    predictor = get_predictor(data_dir)
    await predictor.start()
    return predictor


async def stop_prediction_service():
    """停止预判服务"""
    global _global_predictor
    if _global_predictor:
        await _global_predictor.stop()
        _global_predictor = None


# ========== 演示 ==========

async def demo():
    """演示实时预判器功能"""
    print("=" * 60)
    print("林林v5.0 实时预判触发器 v5.0 演示")
    print("=" * 60)
    
    # 创建预判器
    predictor = RealtimePredictor()
    
    # 设置回调
    def on_suggestion(suggestions):
        print(f"\n[主动建议] 收到 {len(suggestions)} 个建议:")
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s.predicted_need} (置信度: {s.confidence})")
            print(f"     → {s.suggested_action}")
    
    def on_trigger(event_type, predictions):
        print(f"\n[事件触发] {event_type.value} → {len(predictions)} 个预测")
    
    predictor.set_callbacks(on_suggestion, on_trigger)
    
    # 演示1: 对话后分析
    print("\n[演示1] 对话后分析...")
    conversation = {
        "timestamp": datetime.now().isoformat(),
        "content": "帮我看看今天有什么重要邮件",
        "user_id": "user1"
    }
    
    predictions = await predictor.on_conversation_end(conversation)
    print(f"生成 {len(predictions)} 个预测")
    
    # 演示2: 模拟上下文
    print("\n[演示2] 设置上下文数据...")
    predictor.context_cache["emails"] = [
        {"id": "em1", "subject": "紧急: 项目截止日", "unread": True, "urgent": True},
        {"id": "em2", "subject": "会议邀请", "unread": True, "urgent": False},
        {"id": "em3", "subject": "周报提醒", "unread": True, "urgent": False},
    ]
    predictor.context_cache["calendar"] = [
        {"id": "cal1", "title": "项目评审会议", "start_time": "2026-02-11T10:00:00"},
    ]
    
    # 演示3: 手动触发定时检查
    print("\n[演示3] 手动执行定时检查...")
    predictions = await predictor.run_scheduled_check()
    print(f"生成 {len(predictions)} 个预测")
    
    # 演示4: 日历事件触发
    print("\n[演示4] 日历事件触发...")
    event = {"id": "cal2", "title": "周报汇报", "start_time": "2026-02-11T15:00:00"}
    predictions = await predictor.on_calendar_event(event)
    print(f"生成 {len(predictions)} 个预测")
    
    # 演示5: 邮件到达触发
    print("\n[演示5] 邮件到达触发...")
    new_emails = [
        {"id": "em4", "subject": "重要通知", "unread": True, "urgent": True},
    ]
    predictions = await predictor.on_email_arrival(new_emails)
    print(f"生成 {len(predictions)} 个预测")
    
    # 显示统计
    print("\n[统计信息]")
    stats = predictor.get_stats()
    print(f"对话历史数: {stats['conversation_history_count']}")
    print(f"预测报告: {stats['prediction_report']}")
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())
