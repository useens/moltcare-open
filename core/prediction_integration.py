#!/usr/bin/env python3
"""
林林v5.0 预判引擎核心集成模块 (Prediction Integration Core)
版本: v5.0
目标: 将预判引擎深度集成到系统核心流程

核心功能:
1. 实时预判触发 - 每次对话后分析上下文并预测
2. 时间模式学习 - 分析用户24小时活跃模式
3. 上下文关联 - 关联日历/邮件/项目预测需求
4. 预测准确率优化 - A/B测试和持续学习
"""

import json
import os
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import random


class PredictionTriggerType(Enum):
    """预判触发类型"""
    POST_CONVERSATION = "post_conversation"    # 对话后触发
    SCHEDULED = "scheduled"                    # 定时触发
    CONTEXT_CHANGE = "context_change"          # 上下文变化触发
    USER_ACTIVE = "user_active"                # 用户活跃触发
    EVENT_DRIVEN = "event_driven"              # 事件驱动触发


class PredictionContextType(Enum):
    """预测上下文类型"""
    CALENDAR = "calendar"
    EMAIL = "email"
    PROJECT = "project"
    TASK = "task"
    CONVERSATION = "conversation"
    SYSTEM = "system"


@dataclass
class PredictionResult:
    """预测结果"""
    prediction_id: str
    trigger_type: PredictionTriggerType
    predicted_need: str
    confidence: float
    reason: str
    suggested_action: str
    context_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    ab_test_group: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "prediction_id": self.prediction_id,
            "trigger_type": self.trigger_type.value,
            "predicted_need": self.predicted_need,
            "confidence": self.confidence,
            "reason": self.reason,
            "suggested_action": self.suggested_action,
            "context_data": self.context_data,
            "timestamp": self.timestamp.isoformat(),
            "ab_test_group": self.ab_test_group
        }


@dataclass
class TimePattern:
    """时间模式数据"""
    hour: int
    activity_level: float  # 0-1
    request_types: List[str]
    confidence: float
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ContextAssociation:
    """上下文关联"""
    source_type: PredictionContextType
    source_id: str
    related_need: str
    association_strength: float  # 0-1
    trigger_count: int = 0
    success_count: int = 0


class TimePatternLearner:
    """
    时间模式学习器
    分析用户24小时活跃模式，识别周期性需求
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.pattern_file = os.path.join(data_dir, "time_patterns.json")
        self.hourly_patterns: Dict[int, TimePattern] = {}
        self.weekly_patterns: Dict[int, Dict[int, TimePattern]] = defaultdict(dict)  # day -> hour -> pattern
        self.monthly_patterns: Dict[int, List[Dict]] = defaultdict(list)  # day_of_month -> patterns
        self.load_patterns()
    
    def load_patterns(self):
        """加载已学习的时间模式"""
        if os.path.exists(self.pattern_file):
            try:
                with open(self.pattern_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 恢复小时模式
                for hour_str, pattern_data in data.get("hourly", {}).items():
                    hour = int(hour_str)
                    self.hourly_patterns[hour] = TimePattern(
                        hour=hour,
                        activity_level=pattern_data.get("activity_level", 0),
                        request_types=pattern_data.get("request_types", []),
                        confidence=pattern_data.get("confidence", 0)
                    )
                
                # 恢复周模式
                for day_str, hours_data in data.get("weekly", {}).items():
                    day = int(day_str)
                    for hour_str, pattern_data in hours_data.items():
                        hour = int(hour_str)
                        self.weekly_patterns[day][hour] = TimePattern(
                            hour=hour,
                            activity_level=pattern_data.get("activity_level", 0),
                            request_types=pattern_data.get("request_types", []),
                            confidence=pattern_data.get("confidence", 0)
                        )
                        
            except Exception as e:
                print(f"[时间模式学习器] 加载失败: {e}")
    
    def save_patterns(self):
        """保存时间模式"""
        data = {
            "hourly": {
                str(h): {
                    "activity_level": p.activity_level,
                    "request_types": p.request_types,
                    "confidence": p.confidence,
                    "last_updated": p.last_updated.isoformat()
                }
                for h, p in self.hourly_patterns.items()
            },
            "weekly": {
                str(d): {
                    str(h): {
                        "activity_level": p.activity_level,
                        "request_types": p.request_types,
                        "confidence": p.confidence
                    }
                    for h, p in hours.items()
                }
                for d, hours in self.weekly_patterns.items()
            },
            "updated_at": datetime.now().isoformat()
        }
        
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.pattern_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def learn_from_activity(self, timestamp: datetime, request_type: str, 
                           context: Optional[Dict] = None):
        """从用户活动中学习时间模式"""
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # 更新小时模式
        if hour not in self.hourly_patterns:
            self.hourly_patterns[hour] = TimePattern(
                hour=hour,
                activity_level=0,
                request_types=[],
                confidence=0
            )
        
        pattern = self.hourly_patterns[hour]
        # 使用指数移动平均更新活跃度
        pattern.activity_level = 0.7 * pattern.activity_level + 0.3 * 1.0
        if request_type not in pattern.request_types:
            pattern.request_types.append(request_type)
        pattern.confidence = min(pattern.confidence + 0.05, 1.0)
        pattern.last_updated = datetime.now()
        
        # 更新周模式
        if hour not in self.weekly_patterns[weekday]:
            self.weekly_patterns[weekday][hour] = TimePattern(
                hour=hour,
                activity_level=0,
                request_types=[],
                confidence=0
            )
        
        weekly_pattern = self.weekly_patterns[weekday][hour]
        weekly_pattern.activity_level = 0.7 * weekly_pattern.activity_level + 0.3 * 1.0
        if request_type not in weekly_pattern.request_types:
            weekly_pattern.request_types.append(request_type)
        weekly_pattern.confidence = min(weekly_pattern.confidence + 0.05, 1.0)
        
        self.save_patterns()
    
    def predict_for_time(self, target_time: Optional[datetime] = None) -> List[PredictionResult]:
        """基于时间预测用户需求"""
        if target_time is None:
            target_time = datetime.now()
        
        predictions = []
        hour = target_time.hour
        weekday = target_time.weekday()
        
        # 基于小时模式预测
        if hour in self.hourly_patterns:
            pattern = self.hourly_patterns[hour]
            if pattern.activity_level > 0.3:
                for req_type in pattern.request_types[:3]:  # 前3个请求类型
                    confidence = pattern.activity_level * pattern.confidence
                    if confidence > 0.4:
                        predictions.append(PredictionResult(
                            prediction_id=f"time_{hour}_{req_type}_{int(datetime.now().timestamp())}",
                            trigger_type=PredictionTriggerType.SCHEDULED,
                            predicted_need=req_type,
                            confidence=round(confidence, 2),
                            reason=f"历史数据显示在{hour}:00时段经常有此请求",
                            suggested_action=self._get_action_for_request(req_type),
                            context_data={"hour": hour, "pattern_type": "hourly"}
                        ))
        
        # 基于周模式预测
        if weekday in self.weekly_patterns and hour in self.weekly_patterns[weekday]:
            weekly_pattern = self.weekly_patterns[weekday][hour]
            if weekly_pattern.activity_level > 0.3:
                for req_type in weekly_pattern.request_types[:2]:
                    confidence = weekly_pattern.activity_level * weekly_pattern.confidence * 1.1  # 周模式权重稍高
                    if confidence > 0.4:
                        predictions.append(PredictionResult(
                            prediction_id=f"weekly_{weekday}_{hour}_{req_type}",
                            trigger_type=PredictionTriggerType.SCHEDULED,
                            predicted_need=req_type,
                            confidence=round(min(confidence, 0.95), 2),
                            reason=f"{['周一','周二','周三','周四','周五','周六','周日'][weekday]}{hour}:00时段历史模式",
                            suggested_action=self._get_action_for_request(req_type),
                            context_data={"weekday": weekday, "hour": hour, "pattern_type": "weekly"}
                        ))
        
        # 特殊时间规则
        predictions.extend(self._apply_special_time_rules(target_time))
        
        return sorted(predictions, key=lambda x: x.confidence, reverse=True)
    
    def _apply_special_time_rules(self, current_time: datetime) -> List[PredictionResult]:
        """应用特殊时间规则"""
        predictions = []
        hour = current_time.hour
        weekday = current_time.weekday()
        
        # 早上时段 - 简报需求
        if 7 <= hour <= 9:
            predictions.append(PredictionResult(
                prediction_id=f"morning_briefing_{int(datetime.now().timestamp())}",
                trigger_type=PredictionTriggerType.SCHEDULED,
                predicted_need="daily_briefing",
                confidence=0.75,
                reason="早晨时段，通常需要了解今日安排",
                suggested_action="生成今日简报",
                context_data={"time_segment": "morning"}
            ))
        
        # 周一早上 - 周报需求
        if weekday == 0 and 8 <= hour <= 10:
            predictions.append(PredictionResult(
                prediction_id=f"monday_weekly_{int(datetime.now().timestamp())}",
                trigger_type=PredictionTriggerType.SCHEDULED,
                predicted_need="weekly_summary",
                confidence=0.8,
                reason="周一上午，通常需要回顾上周和规划本周",
                suggested_action="生成周报和本周计划",
                context_data={"weekday": 0, "time_segment": "monday_morning"}
            ))
        
        # 周五下午 - 周末准备
        if weekday == 4 and 15 <= hour <= 17:
            predictions.append(PredictionResult(
                prediction_id=f"friday_wrapup_{int(datetime.now().timestamp())}",
                trigger_type=PredictionTriggerType.SCHEDULED,
                predicted_need="week_wrap_up",
                confidence=0.7,
                reason="周五下午，通常需要总结本周并准备下周",
                suggested_action="总结本周待办事项",
                context_data={"weekday": 4, "time_segment": "friday_afternoon"}
            ))
        
        # 深夜时段 - 勿扰模式
        if hour >= 22 or hour <= 6:
            predictions.append(PredictionResult(
                prediction_id=f"rest_mode_{int(datetime.now().timestamp())}",
                trigger_type=PredictionTriggerType.SCHEDULED,
                predicted_need="rest_mode",
                confidence=0.9,
                reason="深夜/凌晨时段，进入勿扰模式",
                suggested_action="减少主动打扰，仅处理紧急事项",
                context_data={"time_segment": "night"}
            ))
        
        return predictions
    
    def _get_action_for_request(self, request_type: str) -> str:
        """获取请求类型对应的建议动作"""
        actions = {
            "email_digest": "生成邮件摘要报告",
            "daily_briefing": "准备今日简报",
            "weekly_summary": "生成周报",
            "task_review": "查看任务列表",
            "search": "执行搜索",
            "schedule": "检查日程安排",
            "reminder": "检查提醒事项",
            "document": "查找相关文档",
            "analysis": "生成分析报告",
            "code": "提供代码协助",
            "general": "提供相关帮助"
        }
        return actions.get(request_type, "提供相关帮助")
    
    def get_active_hours_report(self) -> Dict:
        """获取活跃时段报告"""
        if not self.hourly_patterns:
            return {"status": "insufficient_data", "message": "数据不足"}
        
        # 排序活跃度
        sorted_hours = sorted(
            self.hourly_patterns.items(),
            key=lambda x: x[1].activity_level,
            reverse=True
        )
        
        return {
            "peak_hours": [h for h, p in sorted_hours[:5]],
            "quiet_hours": [h for h, p in sorted_hours[-5:]],
            "most_common_requests": self._get_common_requests(),
            "pattern_count": len(self.hourly_patterns),
            "confidence_avg": sum(p.confidence for p in self.hourly_patterns.values()) / len(self.hourly_patterns)
        }
    
    def _get_common_requests(self) -> List[Tuple[str, int]]:
        """获取最常见的请求类型"""
        request_counts = defaultdict(int)
        for pattern in self.hourly_patterns.values():
            for req in pattern.request_types:
                request_counts[req] += 1
        return sorted(request_counts.items(), key=lambda x: x[1], reverse=True)[:5]


class ContextAssociationEngine:
    """
    上下文关联引擎
    关联日历事件、邮件、项目，预测用户潜在需求
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.association_file = os.path.join(data_dir, "context_associations.json")
        self.associations: Dict[str, ContextAssociation] = {}
        self.load_associations()
    
    def load_associations(self):
        """加载上下文关联数据"""
        if os.path.exists(self.association_file):
            try:
                with open(self.association_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for key, assoc_data in data.get("associations", {}).items():
                    self.associations[key] = ContextAssociation(
                        source_type=PredictionContextType(assoc_data["source_type"]),
                        source_id=assoc_data["source_id"],
                        related_need=assoc_data["related_need"],
                        association_strength=assoc_data["association_strength"],
                        trigger_count=assoc_data.get("trigger_count", 0),
                        success_count=assoc_data.get("success_count", 0)
                    )
            except Exception as e:
                print(f"[上下文关联引擎] 加载失败: {e}")
    
    def save_associations(self):
        """保存上下文关联数据"""
        data = {
            "associations": {
                key: {
                    "source_type": assoc.source_type.value,
                    "source_id": assoc.source_id,
                    "related_need": assoc.related_need,
                    "association_strength": assoc.association_strength,
                    "trigger_count": assoc.trigger_count,
                    "success_count": assoc.success_count
                }
                for key, assoc in self.associations.items()
            },
            "updated_at": datetime.now().isoformat()
        }
        
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.association_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def learn_association(self, source_type: PredictionContextType, source_id: str,
                         related_need: str, was_successful: bool = True):
        """学习上下文关联"""
        key = f"{source_type.value}:{source_id}:{related_need}"
        
        if key not in self.associations:
            self.associations[key] = ContextAssociation(
                source_type=source_type,
                source_id=source_id,
                related_need=related_need,
                association_strength=0.1
            )
        
        assoc = self.associations[key]
        assoc.trigger_count += 1
        
        if was_successful:
            assoc.success_count += 1
            # 成功时增强关联强度
            assoc.association_strength = min(
                assoc.association_strength + 0.1,
                1.0
            )
        else:
            # 失败时减弱关联强度
            assoc.association_strength = max(
                assoc.association_strength - 0.05,
                0.0
            )
        
        self.save_associations()
    
    def predict_from_calendar(self, events: List[Dict]) -> List[PredictionResult]:
        """基于日历事件预测需求"""
        predictions = []
        
        for event in events:
            event_id = event.get("id", "")
            event_title = event.get("title", "").lower()
            event_type = event.get("type", "")
            start_time = event.get("start_time")
            
            # 检查已知关联
            for key, assoc in self.associations.items():
                if assoc.source_type == PredictionContextType.CALENDAR:
                    # 检查事件标题匹配
                    if assoc.source_id in event_title:
                        confidence = assoc.association_strength
                        if assoc.trigger_count > 0:
                            success_rate = assoc.success_count / assoc.trigger_count
                            confidence *= (0.5 + 0.5 * success_rate)
                        
                        if confidence > 0.3:
                            predictions.append(PredictionResult(
                                prediction_id=f"cal_{event_id}_{assoc.related_need}",
                                trigger_type=PredictionTriggerType.EVENT_DRIVEN,
                                predicted_need=assoc.related_need,
                                confidence=round(confidence, 2),
                                reason=f"日历事件'{event_title}'关联",
                                suggested_action=self._get_action_for_context(assoc.related_need),
                                context_data={"event": event, "association_key": key}
                            ))
            
            # 基于事件类型的启发式预测
            heuristics = self._get_calendar_heuristics(event)
            predictions.extend(heuristics)
        
        return predictions
    
    def predict_from_emails(self, emails: List[Dict]) -> List[PredictionResult]:
        """基于邮件预测需求"""
        predictions = []
        
        unread_count = sum(1 for e in emails if e.get("unread", False))
        urgent_count = sum(1 for e in emails if e.get("urgent", False))
        
        # 基于邮件数量的预测
        if unread_count > 10:
            predictions.append(PredictionResult(
                prediction_id=f"email_overflow_{int(datetime.now().timestamp())}",
                trigger_type=PredictionTriggerType.CONTEXT_CHANGE,
                predicted_need="email_digest",
                confidence=min(0.6 + unread_count * 0.02, 0.9),
                reason=f"有{unread_count}封未读邮件",
                suggested_action="生成邮件摘要报告",
                context_data={"unread_count": unread_count}
            ))
        elif unread_count > 5:
            predictions.append(PredictionResult(
                prediction_id=f"email_buildup_{int(datetime.now().timestamp())}",
                trigger_type=PredictionTriggerType.CONTEXT_CHANGE,
                predicted_need="email_brief",
                confidence=0.65,
                reason=f"有{unread_count}封未读邮件",
                suggested_action="提示未读邮件并生成简要摘要",
                context_data={"unread_count": unread_count}
            ))
        
        # 紧急邮件
        if urgent_count > 0:
            predictions.append(PredictionResult(
                prediction_id=f"email_urgent_{int(datetime.now().timestamp())}",
                trigger_type=PredictionTriggerType.EVENT_DRIVEN,
                predicted_need="urgent_email_attention",
                confidence=0.85,
                reason=f"有{urgent_count}封紧急邮件",
                suggested_action="优先处理紧急邮件",
                context_data={"urgent_count": urgent_count}
            ))
        
        # 检查邮件关键词触发关联
        for email in emails[:5]:  # 只检查前5封
            subject = email.get("subject", "").lower()
            for key, assoc in self.associations.items():
                if assoc.source_type == PredictionContextType.EMAIL:
                    if assoc.source_id in subject:
                        predictions.append(PredictionResult(
                            prediction_id=f"email_kw_{email.get('id', '')}",
                            trigger_type=PredictionTriggerType.CONTEXT_CHANGE,
                            predicted_need=assoc.related_need,
                            confidence=assoc.association_strength,
                            reason=f"邮件主题'{subject}'触发关联",
                            suggested_action=self._get_action_for_context(assoc.related_need),
                            context_data={"email": email}
                        ))
        
        return predictions
    
    def predict_from_projects(self, projects: List[Dict]) -> List[PredictionResult]:
        """基于项目状态预测需求"""
        predictions = []
        
        for project in projects:
            project_id = project.get("id", "")
            project_name = project.get("name", "")
            status = project.get("status", "")
            overdue_tasks = project.get("overdue_tasks", 0)
            upcoming_deadline = project.get("upcoming_deadline")
            
            # 检查已知关联
            for key, assoc in self.associations.items():
                if assoc.source_type == PredictionContextType.PROJECT:
                    if assoc.source_id == project_id:
                        predictions.append(PredictionResult(
                            prediction_id=f"proj_{project_id}_{assoc.related_need}",
                            trigger_type=PredictionTriggerType.CONTEXT_CHANGE,
                            predicted_need=assoc.related_need,
                            confidence=assoc.association_strength,
                            reason=f"项目'{project_name}'关联",
                            suggested_action=self._get_action_for_context(assoc.related_need),
                            context_data={"project": project}
                        ))
            
            # 基于项目状态的启发式预测
            if overdue_tasks > 0:
                predictions.append(PredictionResult(
                    prediction_id=f"proj_overdue_{project_id}",
                    trigger_type=PredictionTriggerType.CONTEXT_CHANGE,
                    predicted_need="task_prioritization",
                    confidence=min(0.5 + overdue_tasks * 0.1, 0.85),
                    reason=f"项目'{project_name}'有{overdue_tasks}个逾期任务",
                    suggested_action="处理逾期任务并重新排序",
                    context_data={"project": project, "overdue_tasks": overdue_tasks}
                ))
            
            if upcoming_deadline:
                days_until = (datetime.fromisoformat(upcoming_deadline) - datetime.now()).days
                if days_until <= 3:
                    predictions.append(PredictionResult(
                        prediction_id=f"proj_deadline_{project_id}",
                        trigger_type=PredictionTriggerType.EVENT_DRIVEN,
                        predicted_need="deadline_prep",
                        confidence=0.8 if days_until <= 1 else 0.7,
                        reason=f"项目'{project_name}'截止日临近({days_until}天)",
                        suggested_action="准备截止日相关材料",
                        context_data={"project": project, "days_until": days_until}
                    ))
        
        return predictions
    
    def _get_calendar_heuristics(self, event: Dict) -> List[PredictionResult]:
        """获取日历启发式预测"""
        predictions = []
        title = event.get("title", "").lower()
        
        # 会议相关
        if any(kw in title for kw in ["会议", "meeting", "讨论", "评审"]):
            predictions.append(PredictionResult(
                prediction_id=f"cal_meeting_{event.get('id', '')}",
                trigger_type=PredictionTriggerType.EVENT_DRIVEN,
                predicted_need="meeting_prep",
                confidence=0.75,
                reason=f"即将开始会议: {title}",
                suggested_action="准备会议材料和相关文档",
                context_data={"event": event}
            ))
        
        # 汇报相关
        if any(kw in title for kw in ["汇报", "报告", "汇报", "review"]):
            predictions.append(PredictionResult(
                prediction_id=f"cal_report_{event.get('id', '')}",
                trigger_type=PredictionTriggerType.EVENT_DRIVEN,
                predicted_need="report_prep",
                confidence=0.8,
                reason=f"即将进行汇报: {title}",
                suggested_action="准备汇报材料",
                context_data={"event": event}
            ))
        
        return predictions
    
    def _get_action_for_context(self, need: str) -> str:
        """获取上下文相关的建议动作"""
        actions = {
            "meeting_prep": "准备会议材料",
            "report_prep": "准备汇报材料",
            "deadline_prep": "准备截止日交付物",
            "email_digest": "生成邮件摘要",
            "task_prioritization": "重新排序任务",
            "urgent_email_attention": "优先处理紧急邮件"
        }
        return actions.get(need, "提供相关帮助")


class ABTestOptimizer:
    """
    A/B测试优化器
    测试不同预测策略，动态调整置信度阈值
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.ab_test_file = os.path.join(data_dir, "ab_test_results.json")
        self.threshold_file = os.path.join(data_dir, "dynamic_thresholds.json")
        
        # A/B测试组
        self.test_groups = {
            "control": {"threshold": 0.7, "strategy": "standard"},
            "treatment_a": {"threshold": 0.6, "strategy": "aggressive"},
            "treatment_b": {"threshold": 0.8, "strategy": "conservative"}
        }
        
        # 用户分组 (基于用户ID哈希)
        self.user_group = None
        
        # 测试结果
        self.test_results: Dict[str, List[Dict]] = defaultdict(list)
        
        # 动态阈值
        self.dynamic_thresholds: Dict[str, float] = {}
        
        self.load_data()
    
    def load_data(self):
        """加载A/B测试数据"""
        if os.path.exists(self.ab_test_file):
            try:
                with open(self.ab_test_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.test_results = defaultdict(list, data.get("results", {}))
            except Exception as e:
                print(f"[A/B测试优化器] 加载结果失败: {e}")
        
        if os.path.exists(self.threshold_file):
            try:
                with open(self.threshold_file, 'r', encoding='utf-8') as f:
                    self.dynamic_thresholds = json.load(f)
            except Exception as e:
                print(f"[A/B测试优化器] 加载阈值失败: {e}")
    
    def save_data(self):
        """保存A/B测试数据"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        with open(self.ab_test_file, 'w', encoding='utf-8') as f:
            json.dump({
                "results": dict(self.test_results),
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        with open(self.threshold_file, 'w', encoding='utf-8') as f:
            json.dump(self.dynamic_thresholds, f, ensure_ascii=False, indent=2)
    
    def assign_group(self, user_id: str) -> str:
        """为用户分配A/B测试组"""
        if self.user_group is None:
            # 基于用户ID哈希分配组
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            groups = list(self.test_groups.keys())
            self.user_group = groups[hash_val % len(groups)]
        return self.user_group
    
    def get_threshold(self, prediction_type: str = "default") -> float:
        """获取动态阈值"""
        # 优先使用动态阈值
        if prediction_type in self.dynamic_thresholds:
            return self.dynamic_thresholds[prediction_type]
        
        # 否则使用A/B测试组阈值
        if self.user_group:
            return self.test_groups[self.user_group]["threshold"]
        
        return 0.7  # 默认阈值
    
    def record_result(self, group: str, prediction: PredictionResult, 
                     was_accepted: bool, actual_need: Optional[str] = None):
        """记录A/B测试结果"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "prediction_id": prediction.prediction_id,
            "predicted_need": prediction.predicted_need,
            "confidence": prediction.confidence,
            "was_accepted": was_accepted,
            "actual_need": actual_need
        }
        
        self.test_results[group].append(result)
        self.save_data()
        
        # 更新动态阈值
        self._update_dynamic_threshold(prediction.predicted_need)
    
    def _update_dynamic_threshold(self, prediction_type: str):
        """基于历史表现更新动态阈值"""
        # 收集所有组的该类型预测结果
        all_results = []
        for group, results in self.test_results.items():
            for r in results:
                if r.get("predicted_need") == prediction_type:
                    all_results.append(r)
        
        if len(all_results) < 10:
            return  # 数据不足
        
        # 计算不同阈值下的接受率
        threshold_acceptance = {}
        for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
            filtered = [r for r in all_results if r.get("confidence", 0) >= threshold]
            if filtered:
                acceptance_rate = sum(1 for r in filtered if r.get("was_accepted")) / len(filtered)
                threshold_acceptance[threshold] = acceptance_rate
        
        # 选择最佳阈值（接受率在0.6-0.8之间）
        best_threshold = 0.7
        best_score = 0
        
        for threshold, acceptance in threshold_acceptance.items():
            # 分数 = 接受率 * (1 - |接受率 - 0.7|)  # 最优接受率约为70%
            score = acceptance * (1 - abs(acceptance - 0.7))
            if score > best_score:
                best_score = score
                best_threshold = threshold
        
        self.dynamic_thresholds[prediction_type] = best_threshold
        self.save_data()
    
    def get_ab_test_report(self) -> Dict:
        """获取A/B测试报告"""
        report = {
            "groups": {},
            "overall": {},
            "recommendations": []
        }
        
        for group, results in self.test_results.items():
            if not results:
                continue
            
            total = len(results)
            accepted = sum(1 for r in results if r.get("was_accepted"))
            
            report["groups"][group] = {
                "total_predictions": total,
                "accepted": accepted,
                "acceptance_rate": round(accepted / total, 3) if total > 0 else 0,
                "avg_confidence": round(sum(r.get("confidence", 0) for r in results) / total, 3) if total > 0 else 0
            }
        
        # 找出最佳组
        if report["groups"]:
            best_group = max(report["groups"].items(), key=lambda x: x[1]["acceptance_rate"])
            report["recommendations"].append(
                f"建议采用 '{best_group[0]}' 组的策略，接受率为 {best_group[1]['acceptance_rate']:.1%}"
            )
        
        # 动态阈值建议
        report["dynamic_thresholds"] = self.dynamic_thresholds
        
        return report


class PredictionIntegration:
    """
    预判引擎集成主类
    整合时间模式学习、上下文关联和A/B测试优化
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.time_learner = TimePatternLearner(data_dir)
        self.context_engine = ContextAssociationEngine(data_dir)
        self.ab_optimizer = ABTestOptimizer(data_dir)
        
        # 回调函数
        self.on_prediction: Optional[Callable[[PredictionResult], None]] = None
        self.on_suggestion: Optional[Callable[[List[PredictionResult]], None]] = None
        
        # 预测历史
        self.recent_predictions: List[PredictionResult] = []
        self.max_history = 100
        
        # 冷却时间跟踪
        self.suggestion_cooldown: Dict[str, datetime] = {}
        self.cooldown_hours = 4
    
    def set_callbacks(self, 
                     on_prediction: Optional[Callable[[PredictionResult], None]] = None,
                     on_suggestion: Optional[Callable[[List[PredictionResult]], None]] = None):
        """设置回调函数"""
        self.on_prediction = on_prediction
        self.on_suggestion = on_suggestion
    
    async def analyze_conversation(self, conversation: Dict, 
                                   context: Optional[Dict] = None) -> List[PredictionResult]:
        """
        分析对话并生成预测
        每次对话后调用此函数
        """
        predictions = []
        
        # 1. 从对话内容学习时间模式
        timestamp = datetime.fromisoformat(conversation.get("timestamp", datetime.now().isoformat()))
        content = conversation.get("content", "")
        request_type = self._classify_request(content)
        
        self.time_learner.learn_from_activity(timestamp, request_type, context)
        
        # 2. 基于时间生成预测
        time_predictions = self.time_learner.predict_for_time()
        predictions.extend(time_predictions)
        
        # 3. 基于上下文生成预测
        if context:
            if "calendar" in context:
                cal_predictions = self.context_engine.predict_from_calendar(context["calendar"])
                predictions.extend(cal_predictions)
            
            if "emails" in context:
                email_predictions = self.context_engine.predict_from_emails(context["emails"])
                predictions.extend(email_predictions)
            
            if "projects" in context:
                proj_predictions = self.context_engine.predict_from_projects(context["projects"])
                predictions.extend(proj_predictions)
        
        # 4. 过滤和排序
        filtered = self._filter_predictions(predictions)
        
        # 5. 应用A/B测试分组
        user_id = context.get("user_id", "default") if context else "default"
        group = self.ab_optimizer.assign_group(user_id)
        for pred in filtered:
            pred.ab_test_group = group
        
        # 6. 记录预测历史
        self.recent_predictions.extend(filtered)
        self.recent_predictions = self.recent_predictions[-self.max_history:]
        
        # 7. 触发回调
        if self.on_prediction and filtered:
            for pred in filtered[:3]:  # 只触发前3个
                self.on_prediction(pred)
        
        if self.on_suggestion and filtered:
            self.on_suggestion(filtered[:3])
        
        return filtered
    
    async def generate_proactive_suggestions(self, 
                                            context: Optional[Dict] = None) -> List[PredictionResult]:
        """
        生成主动建议
        高置信度时主动提供给用户
        """
        predictions = []
        
        # 1. 时间预测
        time_predictions = self.time_learner.predict_for_time()
        predictions.extend(time_predictions)
        
        # 2. 上下文预测
        if context:
            if "calendar" in context:
                predictions.extend(self.context_engine.predict_from_calendar(context["calendar"]))
            if "emails" in context:
                predictions.extend(self.context_engine.predict_from_emails(context["emails"]))
            if "projects" in context:
                predictions.extend(self.context_engine.predict_from_projects(context["projects"]))
        
        # 3. 过滤低置信度和冷却中的建议
        threshold = self.ab_optimizer.get_threshold()
        filtered = [p for p in predictions if p.confidence >= threshold]
        filtered = self._apply_cooldown(filtered)
        
        # 4. 排序并限制数量
        filtered.sort(key=lambda x: x.confidence, reverse=True)
        top_suggestions = filtered[:3]
        
        # 5. 更新冷却时间
        for sugg in top_suggestions:
            self.suggestion_cooldown[sugg.predicted_need] = datetime.now()
        
        return top_suggestions
    
    def record_feedback(self, prediction_id: str, was_accurate: bool, 
                       actual_need: Optional[str] = None, was_accepted: bool = False):
        """
        记录用户反馈
        用于持续学习和优化
        """
        # 找到对应的预测
        prediction = None
        for p in self.recent_predictions:
            if p.prediction_id == prediction_id:
                prediction = p
                break
        
        if not prediction:
            return
        
        # 记录A/B测试结果
        if prediction.ab_test_group:
            self.ab_optimizer.record_result(
                prediction.ab_test_group,
                prediction,
                was_accepted,
                actual_need
            )
        
        # 学习上下文关联
        if actual_need and actual_need != prediction.predicted_need:
            # 预测错误，学习关联
            for ctx_type, ctx_data in prediction.context_data.items():
                if ctx_type == "event":
                    self.context_engine.learn_association(
                        PredictionContextType.CALENDAR,
                        ctx_data.get("id", ""),
                        actual_need,
                        was_successful=True
                    )
    
    def _classify_request(self, content: str) -> str:
        """分类请求类型"""
        content_lower = content.lower()
        
        patterns = {
            "email_digest": [r"邮件", r"email", r"收件箱", r"inbox"],
            "daily_briefing": [r"简报", r"总结", r"summary", r"今日", r"今天"],
            "search": [r"搜索", r"查找", r"find", r"search", r"查一下"],
            "schedule": [r"日程", r"日程安排", r"会议", r"calendar", r"schedule"],
            "task": [r"任务", r"todo", r"待办", r"task"],
            "reminder": [r"提醒", r"remind", r"别忘了"],
            "document": [r"文档", r"doc", r"文件", r"file"],
            "analysis": [r"分析", r"统计", r"analytics", r"report"],
            "code": [r"代码", r"code", r"编程", r"programming", r"写个脚本"]
        }
        
        for req_type, keywords in patterns.items():
            for keyword in keywords:
                if re.search(keyword, content_lower):
                    return req_type
        
        return "general"
    
    def _filter_predictions(self, predictions: List[PredictionResult]) -> List[PredictionResult]:
        """过滤预测结果"""
        threshold = self.ab_optimizer.get_threshold()
        
        # 按置信度过滤
        filtered = [p for p in predictions if p.confidence >= threshold]
        
        # 去重（相同predicted_need保留置信度最高的）
        seen = {}
        for p in filtered:
            if p.predicted_need not in seen or seen[p.predicted_need].confidence < p.confidence:
                seen[p.predicted_need] = p
        
        return list(seen.values())
    
    def _apply_cooldown(self, predictions: List[PredictionResult]) -> List[PredictionResult]:
        """应用冷却时间过滤"""
        now = datetime.now()
        result = []
        
        for p in predictions:
            last_shown = self.suggestion_cooldown.get(p.predicted_need)
            if last_shown:
                hours_since = (now - last_shown).total_seconds() / 3600
                if hours_since < self.cooldown_hours:
                    continue  # 还在冷却期
            result.append(p)
        
        return result
    
    def get_prediction_report(self) -> Dict:
        """获取预测系统报告"""
        return {
            "time_patterns": self.time_learner.get_active_hours_report(),
            "context_associations": len(self.context_engine.associations),
            "ab_test": self.ab_optimizer.get_ab_test_report(),
            "recent_predictions": len(self.recent_predictions),
            "threshold": self.ab_optimizer.get_threshold()
        }


# ========== 便捷函数 ==========

def create_prediction_integration(data_dir: str = "data") -> PredictionIntegration:
    """创建预判引擎集成实例"""
    return PredictionIntegration(data_dir)


async def demo():
    """演示预判引擎集成功能"""
    print("=" * 60)
    print("林林v5.0 预判引擎集成 v5.0 演示")
    print("=" * 60)
    
    integration = create_prediction_integration()
    
    # 设置回调
    def on_prediction(pred: PredictionResult):
        print(f"\n[预测回调] {pred.predicted_need} (置信度: {pred.confidence})")
    
    def on_suggestion(suggestions: List[PredictionResult]):
        print(f"\n[建议回调] 收到 {len(suggestions)} 个建议")
    
    integration.set_callbacks(on_prediction, on_suggestion)
    
    # 模拟历史对话数据
    print("\n[1] 学习时间模式...")
    sample_conversations = [
        {"timestamp": "2026-02-10T08:30:00", "content": "今天有什么安排？"},
        {"timestamp": "2026-02-10T08:45:00", "content": "帮我总结一下昨天的邮件"},
        {"timestamp": "2026-02-10T14:00:00", "content": "搜索一下相关资料"},
        {"timestamp": "2026-02-09T08:15:00", "content": "早上好，今日简报"},
        {"timestamp": "2026-02-09T08:20:00", "content": "邮件摘要"},
        {"timestamp": "2026-02-08T08:00:00", "content": "今天有什么任务？"},
        {"timestamp": "2026-02-03T08:30:00", "content": "周一简报"},
        {"timestamp": "2026-02-03T14:00:00", "content": "周报生成"},
    ]
    
    for conv in sample_conversations:
        await integration.analyze_conversation(conv)
    
    print("时间模式学习完成")
    
    # 测试上下文预测
    print("\n[2] 测试上下文预测...")
    context = {
        "calendar": [
            {"id": "cal1", "title": "项目评审会议", "start_time": "2026-02-11T10:00:00", "type": "meeting"},
            {"id": "cal2", "title": "周报汇报", "start_time": "2026-02-11T15:00:00", "type": "report"}
        ],
        "emails": [
            {"id": "em1", "subject": "紧急: 项目截止日提醒", "unread": True, "urgent": True},
            {"id": "em2", "subject": "会议邀请", "unread": True, "urgent": False},
            {"id": "em3", "subject": "周报模板", "unread": True, "urgent": False},
        ],
        "projects": [
            {"id": "proj1", "name": "AI系统开发", "status": "active", "overdue_tasks": 2, "upcoming_deadline": "2026-02-15T23:59:59"}
        ]
    }
    
    suggestions = await integration.generate_proactive_suggestions(context)
    print(f"\n生成 {len(suggestions)} 个主动建议:")
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. [{s.trigger_type.value}] {s.predicted_need}")
        print(f"     置信度: {s.confidence} | {s.reason}")
        print(f"     建议: {s.suggested_action}")
    
    # 显示报告
    print("\n[3] 预测系统报告...")
    report = integration.get_prediction_report()
    print(f"时间模式: {report['time_patterns']}")
    print(f"上下文关联数: {report['context_associations']}")
    print(f"当前阈值: {report['threshold']}")
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())
