#!/usr/bin/env python3
"""
林林v5.0 预判引擎核心 (Prediction Engine Core)
版本: v0.1
目标: 在用户开口前预测需求并主动满足
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import hashlib


class PredictionEngine:
    """
    预判引擎核心类
    
    职责:
    1. 分析用户行为模式
    2. 预测用户需求
    3. 生成主动建议
    4. 记录反馈并学习
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.user_pattern_file = os.path.join(data_dir, "user_pattern.json")
        self.user_pattern = self._load_user_pattern()
        self.prediction_threshold = 0.7  # 预测准确率阈值
        self.suggestion_cooldown = {}    # 建议冷却时间记录
        
    def _load_user_pattern(self) -> Dict:
        """加载用户模式数据"""
        if os.path.exists(self.user_pattern_file):
            try:
                with open(self.user_pattern_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[预判引擎] 加载用户模式失败: {e}")
                return self._init_default_pattern()
        return self._init_default_pattern()
    
    def _init_default_pattern(self) -> Dict:
        """初始化默认用户模式"""
        return {
            "version": "0.1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "behavior_patterns": {
                "hourly_activity": defaultdict(lambda: {"count": 0, "requests": []}),
                "day_of_week": defaultdict(lambda: {"count": 0, "requests": []}),
                "request_types": defaultdict(lambda: {"count": 0, "timestamps": []}),
                "work_rhythm": {
                    "deep_work_hours": [],
                    "break_hours": [],
                    "high_frequency_periods": []
                }
            },
            "preferences": {
                "communication_style": "concise",  # concise/detailed/casual
                "notification_preference": "moderate",  # aggressive/moderate/minimal
                "preferred_topics": [],
                "avoided_topics": []
            },
            "prediction_rules": [],
            "feedback_history": [],
            "prediction_accuracy": {
                "total_predictions": 0,
                "correct_predictions": 0,
                "accuracy_rate": 0.0
            }
        }
    
    def save_user_pattern(self):
        """保存用户模式数据"""
        self.user_pattern["updated_at"] = datetime.now().isoformat()
        
        # 转换为可JSON序列化的格式
        pattern_copy = json.loads(json.dumps(self.user_pattern, default=str))
        
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.user_pattern_file, 'w', encoding='utf-8') as f:
            json.dump(pattern_copy, f, ensure_ascii=False, indent=2)
    
    # ========== 1. 用户行为模式分析 ==========
    
    def analyze_active_hours(self, conversations: List[Dict]) -> Dict:
        """
        分析用户活跃时间段
        
        Args:
            conversations: 历史对话列表，每项包含timestamp和内容
            
        Returns:
            活跃时间段统计
        """
        hourly_stats = defaultdict(int)
        request_types_by_hour = defaultdict(list)
        
        for conv in conversations:
            ts = datetime.fromisoformat(conv.get("timestamp", datetime.now().isoformat()))
            hour = ts.hour
            hourly_stats[hour] += 1
            
            # 提取请求类型
            request_type = self._classify_request(conv.get("content", ""))
            request_types_by_hour[hour].append(request_type)
        
        # 找出高频时段
        total = sum(hourly_stats.values())
        active_hours = {}
        for hour in range(24):
            count = hourly_stats.get(hour, 0)
            if count > 0:
                active_hours[hour] = {
                    "count": count,
                    "percentage": round(count / total * 100, 2),
                    "top_requests": self._get_top_items(request_types_by_hour[hour], 3)
                }
        
        # 更新用户模式
        self.user_pattern["behavior_patterns"]["hourly_activity"] = dict(active_hours)
        
        return {
            "active_hours": active_hours,
            "peak_hour": max(hourly_stats.keys(), key=lambda h: hourly_stats[h]) if hourly_stats else None,
            "quiet_hours": [h for h in range(24) if hourly_stats.get(h, 0) == 0]
        }
    
    def identify_request_patterns(self, conversations: List[Dict]) -> Dict:
        """
        识别高频请求类型和时机
        
        Args:
            conversations: 历史对话列表
            
        Returns:
            请求模式统计
        """
        request_stats = defaultdict(lambda: {"count": 0, "timestamps": [], "contexts": []})
        
        for conv in conversations:
            content = conv.get("content", "")
            request_type = self._classify_request(content)
            ts = conv.get("timestamp", datetime.now().isoformat())
            
            request_stats[request_type]["count"] += 1
            request_stats[request_type]["timestamps"].append(ts)
            request_stats[request_type]["contexts"].append(content[:100])  # 保存前100字符作为上下文
        
        # 分析周期性模式
        patterns = []
        for req_type, stats in request_stats.items():
            if stats["count"] >= 3:  # 至少3次才算模式
                # 检查是否有周期性
                timestamps = [datetime.fromisoformat(ts) for ts in stats["timestamps"]]
                periodicity = self._analyze_periodicity(timestamps)
                
                patterns.append({
                    "request_type": req_type,
                    "frequency": stats["count"],
                    "periodicity": periodicity,
                    "last_occurrence": max(stats["timestamps"]) if stats["timestamps"] else None
                })
        
        # 更新用户模式
        self.user_pattern["behavior_patterns"]["request_types"] = dict(request_stats)
        
        return {
            "patterns": sorted(patterns, key=lambda x: x["frequency"], reverse=True),
            "total_requests": sum(stats["count"] for stats in request_stats.values())
        }
    
    def detect_work_rhythm(self, conversations: List[Dict]) -> Dict:
        """
        检测用户的工作节奏（深度工作/休息）
        
        Args:
            conversations: 历史对话列表
            
        Returns:
            工作节奏分析
        """
        hourly_intensity = defaultdict(lambda: {"messages": 0, "complexity": 0})
        
        for conv in conversations:
            ts = datetime.fromisoformat(conv.get("timestamp", datetime.now().isoformat()))
            hour = ts.hour
            content = conv.get("content", "")
            
            hourly_intensity[hour]["messages"] += 1
            hourly_intensity[hour]["complexity"] += self._estimate_complexity(content)
        
        # 计算每个小时的平均复杂度
        for hour in hourly_intensity:
            if hourly_intensity[hour]["messages"] > 0:
                hourly_intensity[hour]["avg_complexity"] = (
                    hourly_intensity[hour]["complexity"] / hourly_intensity[hour]["messages"]
                )
        
        # 识别深度工作时段（高频且高复杂度）
        deep_work_hours = []
        break_hours = []
        
        for hour in range(24):
            stats = hourly_intensity.get(hour, {"messages": 0, "avg_complexity": 0})
            msg_count = stats.get("messages", 0)
            avg_complexity = stats.get("avg_complexity", 0)
            
            if msg_count >= 5 and avg_complexity > 3:
                deep_work_hours.append(hour)
            elif msg_count == 0:
                break_hours.append(hour)
        
        rhythm = {
            "deep_work_hours": deep_work_hours,
            "break_hours": break_hours,
            "high_frequency_periods": [
                h for h, s in hourly_intensity.items() 
                if s["messages"] >= 3
            ]
        }
        
        self.user_pattern["behavior_patterns"]["work_rhythm"] = rhythm
        return rhythm
    
    # ========== 2. 需求预测模型 ==========
    
    def predict_by_time(self, current_time: Optional[datetime] = None) -> List[Dict]:
        """
        基于时间预测用户需求
        
        Args:
            current_time: 当前时间，默认为now
            
        Returns:
            预测结果列表
        """
        if current_time is None:
            current_time = datetime.now()
        
        predictions = []
        hour = current_time.hour
        weekday = current_time.weekday()
        
        # 检查历史同期的请求
        hourly_activity = self.user_pattern["behavior_patterns"].get("hourly_activity", {})
        hour_str = str(hour)
        
        if hour_str in hourly_activity:
            activity = hourly_activity[hour_str]
            confidence = min(activity.get("percentage", 0) / 100 * 1.5, 0.95)
            
            if confidence > 0.3:  # 置信度阈值
                predictions.append({
                    "type": "time_based",
                    "predicted_need": activity.get("top_requests", ["general"])[0],
                    "confidence": round(confidence, 2),
                    "reason": f"历史数据显示在{hour}:00时段有活跃请求",
                    "suggested_action": self._get_suggested_action(activity.get("top_requests", ["general"])[0])
                })
        
        # 特殊时间点的预测规则
        special_time_predictions = self._apply_special_time_rules(current_time)
        predictions.extend(special_time_predictions)
        
        return sorted(predictions, key=lambda x: x["confidence"], reverse=True)
    
    def predict_by_context(self, context: Dict) -> List[Dict]:
        """
        基于上下文预测用户需求
        
        Args:
            context: 当前上下文信息，如最近邮件、日程等
            
        Returns:
            预测结果列表
        """
        predictions = []
        
        # 邮件上下文
        if "recent_emails" in context and context["recent_emails"]:
            email_count = len(context["recent_emails"])
            unread_count = sum(1 for e in context["recent_emails"] if e.get("unread", False))
            
            if unread_count > 5:
                predictions.append({
                    "type": "context_based",
                    "predicted_need": "email_digest",
                    "confidence": 0.8,
                    "reason": f"有{unread_count}封未读邮件",
                    "suggested_action": "生成邮件摘要报告"
                })
            elif unread_count > 0:
                predictions.append({
                    "type": "context_based",
                    "predicted_need": "email_brief",
                    "confidence": 0.6,
                    "reason": f"有{unread_count}封未读邮件",
                    "suggested_action": "提示未读邮件数量"
                })
        
        # 日程上下文
        if "upcoming_events" in context and context["upcoming_events"]:
            events = context["upcoming_events"]
            urgent_events = [e for e in events if e.get("urgent", False)]
            
            if urgent_events:
                predictions.append({
                    "type": "context_based",
                    "predicted_need": "meeting_prep",
                    "confidence": 0.85,
                    "reason": f"有{len(urgent_events)}个紧急会议即将到来",
                    "suggested_action": "提供会议准备信息"
                })
        
        # 工作负载上下文
        if "workload" in context:
            workload = context["workload"]
            if workload.get("task_count", 0) > 10:
                predictions.append({
                    "type": "context_based",
                    "predicted_need": "task_prioritization",
                    "confidence": 0.75,
                    "reason": "任务堆积，可能需要优先级排序",
                    "suggested_action": "提供任务优先级建议"
                })
        
        return predictions
    
    def predict_by_history(self, lookback_days: int = 7) -> List[Dict]:
        """
        基于历史模式预测需求
        
        Args:
            lookback_days: 回顾天数
            
        Returns:
            预测结果列表
        """
        predictions = []
        now = datetime.now()
        
        # 检查周期性模式
        request_types = self.user_pattern["behavior_patterns"].get("request_types", {})
        
        for req_type, stats in request_types.items():
            timestamps = stats.get("timestamps", [])
            if len(timestamps) < 3:
                continue
            
            # 检查是否到了该出现的时间
            last_ts = datetime.fromisoformat(max(timestamps))
            periodicity = self._analyze_periodicity(
                [datetime.fromisoformat(ts) for ts in timestamps]
            )
            
            if periodicity.get("pattern") == "weekly":
                days_since_last = (now - last_ts).days
                expected_interval = 7
                
                if abs(days_since_last - expected_interval) <= 1:
                    predictions.append({
                        "type": "history_based",
                        "predicted_need": req_type,
                        "confidence": 0.75,
                        "reason": f"每{expected_interval}天一次的周期性请求",
                        "suggested_action": self._get_suggested_action(req_type)
                    })
        
        # 周模式检查
        weekday = now.weekday()
        if weekday == 0:  # 周一
            predictions.append({
                "type": "history_based",
                "predicted_need": "weekly_summary",
                "confidence": 0.7,
                "reason": "周一通常需要周报或周计划",
                "suggested_action": "生成上周总结和本周计划模板"
            })
        elif weekday == 4:  # 周五
            predictions.append({
                "type": "history_based",
                "predicted_need": "week_wrap_up",
                "confidence": 0.65,
                "reason": "周五通常需要总结本周工作",
                "suggested_action": "提供本周工作总结"
            })
        
        return predictions
    
    # ========== 3. 主动建议生成 ==========
    
    def generate_suggestions(self, context: Optional[Dict] = None) -> List[Dict]:
        """
        生成主动建议
        
        Args:
            context: 当前上下文
            
        Returns:
            建议列表
        """
        all_predictions = []
        
        # 收集所有预测
        all_predictions.extend(self.predict_by_time())
        if context:
            all_predictions.extend(self.predict_by_context(context))
        all_predictions.extend(self.predict_by_history())
        
        # 过滤和排序
        filtered_suggestions = []
        for pred in all_predictions:
            # 过滤低置信度
            if pred["confidence"] < self.prediction_threshold:
                continue
            
            # 检查冷却时间
            pred_key = f"{pred['type']}:{pred['predicted_need']}"
            last_shown = self.suggestion_cooldown.get(pred_key)
            if last_shown and (datetime.now() - last_shown).hours < 4:
                continue  # 4小时内不重复建议
            
            filtered_suggestions.append(pred)
        
        # 按置信度排序，最多返回3个
        filtered_suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        top_suggestions = filtered_suggestions[:3]
        
        # 生成个性化建议内容
        personalized = []
        for sugg in top_suggestions:
            personalized_sugg = self._personalize_suggestion(sugg)
            personalized.append(personalized_sugg)
            
            # 更新冷却时间
            pred_key = f"{sugg['type']}:{sugg['predicted_need']}"
            self.suggestion_cooldown[pred_key] = datetime.now()
        
        return personalized
    
    def _personalize_suggestion(self, suggestion: Dict) -> Dict:
        """个性化建议内容"""
        style = self.user_pattern["preferences"].get("communication_style", "concise")
        
        templates = {
            "concise": {
                "briefing": "简报准备好了，需要查看吗？",
                "email_digest": f"有未读邮件，需要摘要吗？",
                "weekly_summary": "周一了，要看看上周总结吗？",
                "task_prioritization": "任务有点多，帮你排个序？"
            },
            "detailed": {
                "briefing": "根据您的习惯，我为您准备了今天的简报。内容包含您可能关心的重要信息，需要现在查看吗？",
                "email_digest": "检测到有未读邮件堆积，我可以为您生成一份摘要报告，帮助您快速了解重点内容。",
                "weekly_summary": "新的一周开始了。基于上周的数据，我为您准备了总结报告和本周建议。",
                "task_prioritization": "您当前的任务列表较长，我可以根据紧急程度和重要性帮您重新排序，提高工作效率。"
            },
            "casual": {
                "briefing": "嘿，今天的简报来啦！看一眼不？",
                "email_digest": "邮件堆成小山了😅 要我帮你看看有啥重要的不？",
                "weekly_summary": "周一愉快！上周过得怎么样？我给你总结了一下~",
                "task_prioritization": "哇，任务好多！要我帮你理一理吗？"
            }
        }
        
        need = suggestion["predicted_need"]
        message = templates.get(style, templates["concise"]).get(
            need, 
            f"检测到您可能需要{suggestion['suggested_action']}"
        )
        
        return {
            **suggestion,
            "personalized_message": message,
            "communication_style": style,
            "priority": self._calculate_priority(suggestion)
        }
    
    # ========== 4. 学习反馈循环 ==========
    
    def record_feedback(self, prediction_id: str, was_accurate: bool, actual_need: Optional[str] = None):
        """
        记录预测反馈
        
        Args:
            prediction_id: 预测ID
            was_accurate: 是否准确
            actual_need: 实际需求（如果不准确）
        """
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "prediction_id": prediction_id,
            "was_accurate": was_accurate,
            "actual_need": actual_need
        }
        
        self.user_pattern["feedback_history"].append(feedback)
        
        # 更新准确率统计
        stats = self.user_pattern["prediction_accuracy"]
        stats["total_predictions"] += 1
        if was_accurate:
            stats["correct_predictions"] += 1
        stats["accuracy_rate"] = round(
            stats["correct_predictions"] / stats["total_predictions"], 
            3
        )
        
        # 分析误判原因
        if not was_accurate and actual_need:
            self._analyze_mis_prediction(prediction_id, actual_need)
        
        self.save_user_pattern()
    
    def _analyze_mis_prediction(self, prediction_id: str, actual_need: str):
        """分析预测误判原因"""
        # 记录误判模式，用于后续优化
        misprediction_pattern = {
            "prediction_id": prediction_id,
            "actual_need": actual_need,
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果误判次数多，考虑调整规则
        recent_mispredictions = [
            f for f in self.user_pattern["feedback_history"][-20:]
            if not f.get("was_accurate", True)
        ]
        
        if len(recent_mispredictions) >= 5:
            # 误判率过高，可能需要调整阈值
            misrate = len(recent_mispredictions) / 20
            if misrate > 0.4:
                self.prediction_threshold = min(self.prediction_threshold + 0.05, 0.95)
                print(f"[预判引擎] 误判率较高({misrate:.2%})，调整阈值至{self.prediction_threshold}")
    
    def get_learning_report(self) -> Dict:
        """获取学习报告"""
        stats = self.user_pattern["prediction_accuracy"]
        feedback = self.user_pattern["feedback_history"]
        
        return {
            "accuracy_stats": stats,
            "total_feedback_records": len(feedback),
            "recent_accuracy": self._calculate_recent_accuracy(7),
            "top_mispredicted_needs": self._get_top_mispredictions(),
            "improvement_suggestions": self._generate_improvement_suggestions()
        }
    
    # ========== 辅助方法 ==========
    
    def _classify_request(self, content: str) -> str:
        """分类请求类型"""
        content_lower = content.lower()
        
        patterns = {
            "email_digest": [r"邮件", r"email", r"收件箱", r"inbox"],
            "briefing": [r"简报", r"总结", r"summary", r"今日", r"今天"],
            "search": [r"搜索", r"查找", r"find", r"search", r"查一下"],
            "schedule": [r"日程", r"日程安排", r"会议", r"calendar", r"schedule"],
            "task": [r"任务", r"todo", r"待办", r"task"],
            "reminder": [r"提醒", r"remind", r"别忘了"],
            "document": [r"文档", r"doc", r"文件", r"file"],
            "analysis": [r"分析", r"统计", r"analytics", r"report"]
        }
        
        for req_type, keywords in patterns.items():
            for keyword in keywords:
                if re.search(keyword, content_lower):
                    return req_type
        
        return "general"
    
    def _analyze_periodicity(self, timestamps: List[datetime]) -> Dict:
        """分析时间戳的周期性"""
        if len(timestamps) < 3:
            return {"pattern": "unknown", "confidence": 0}
        
        timestamps.sort()
        intervals = [
            (timestamps[i+1] - timestamps[i]).days
            for i in range(len(timestamps) - 1)
        ]
        
        if not intervals:
            return {"pattern": "unknown", "confidence": 0}
        
        avg_interval = sum(intervals) / len(intervals)
        
        # 检查是否接近7天（每周）
        if 6 <= avg_interval <= 8:
            return {"pattern": "weekly", "interval_days": 7, "confidence": 0.8}
        
        # 检查是否接近1天（每天）
        if 0.9 <= avg_interval <= 1.1:
            return {"pattern": "daily", "interval_days": 1, "confidence": 0.9}
        
        return {"pattern": "irregular", "avg_interval_days": avg_interval, "confidence": 0.5}
    
    def _estimate_complexity(self, content: str) -> int:
        """估算请求复杂度（1-5）"""
        # 简单启发式：长度、关键词等
        score = 1
        
        if len(content) > 200:
            score += 1
        if len(content) > 500:
            score += 1
        
        complex_keywords = ["分析", "比较", "评估", "生成", "创建", "优化", "设计"]
        for kw in complex_keywords:
            if kw in content:
                score += 1
                break
        
        return min(score, 5)
    
    def _get_top_items(self, items: List[str], n: int) -> List[str]:
        """获取出现频率最高的n个项"""
        counts = defaultdict(int)
        for item in items:
            counts[item] += 1
        return [item for item, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]]
    
    def _get_suggested_action(self, request_type: str) -> str:
        """根据请求类型获取建议动作"""
        actions = {
            "email_digest": "生成邮件摘要",
            "briefing": "准备简报",
            "search": "执行搜索",
            "schedule": "检查日程",
            "task": "查看任务列表",
            "reminder": "设置提醒",
            "document": "查找相关文档",
            "analysis": "生成分析报告"
        }
        return actions.get(request_type, "提供相关帮助")
    
    def _apply_special_time_rules(self, current_time: datetime) -> List[Dict]:
        """应用特殊时间规则"""
        predictions = []
        hour = current_time.hour
        
        # 早上8-9点：可能需要简报
        if 8 <= hour <= 9:
            predictions.append({
                "type": "time_based",
                "predicted_need": "briefing",
                "confidence": 0.75,
                "reason": "早晨时段，通常需要了解今日安排",
                "suggested_action": "生成今日简报"
            })
        
        # 晚上10点后：进入休息模式
        if hour >= 22 or hour <= 6:
            predictions.append({
                "type": "time_based",
                "predicted_need": "rest_mode",
                "confidence": 0.9,
                "reason": "晚间休息时段，减少打扰",
                "suggested_action": "勿扰模式"
            })
        
        return predictions
    
    def _calculate_priority(self, suggestion: Dict) -> str:
        """计算建议优先级"""
        confidence = suggestion.get("confidence", 0)
        
        if confidence >= 0.85:
            return "high"
        elif confidence >= 0.7:
            return "medium"
        else:
            return "low"
    
    def _calculate_recent_accuracy(self, days: int) -> float:
        """计算最近n天的准确率"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_feedback = [
            f for f in self.user_pattern["feedback_history"]
            if datetime.fromisoformat(f.get("timestamp", "2000-01-01")) > cutoff
        ]
        
        if not recent_feedback:
            return 0.0
        
        correct = sum(1 for f in recent_feedback if f.get("was_accurate", False))
        return round(correct / len(recent_feedback), 3)
    
    def _get_top_mispredictions(self) -> List[Dict]:
        """获取最常见的误判类型"""
        mispredictions = [
            f for f in self.user_pattern["feedback_history"]
            if not f.get("was_accurate", True)
        ]
        
        if not mispredictions:
            return []
        
        from collections import Counter
        actual_needs = [f.get("actual_need", "unknown") for f in mispredictions]
        return [
            {"need": need, "count": count}
            for need, count in Counter(actual_needs).most_common(5)
        ]
    
    def _generate_improvement_suggestions(self) -> List[str]:
        """生成改进建议"""
        suggestions = []
        stats = self.user_pattern["prediction_accuracy"]
        
        if stats["total_predictions"] < 10:
            suggestions.append("预测样本不足，继续收集用户反馈以优化模型")
        
        if stats.get("accuracy_rate", 0) < 0.6:
            suggestions.append("当前准确率偏低，建议调整预测阈值或增加特征")
        
        return suggestions


# ========== 使用示例 ==========

def demo():
    """演示预判引擎功能"""
    engine = PredictionEngine()
    
    # 模拟历史对话数据
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
    
    print("=" * 50)
    print("林林v5.0 预判引擎 v0.1 演示")
    print("=" * 50)
    
    # 1. 分析活跃时段
    print("\n[1] 分析用户活跃时段...")
    active_hours = engine.analyze_active_hours(sample_conversations)
    print(f"活跃时段: {active_hours}")
    
    # 2. 识别请求模式
    print("\n[2] 识别请求模式...")
    patterns = engine.identify_request_patterns(sample_conversations)
    print(f"发现模式: {len(patterns['patterns'])} 个")
    for p in patterns['patterns'][:3]:
        print(f"  - {p['request_type']}: 频率={p['frequency']}")
    
    # 3. 检测工作节奏
    print("\n[3] 检测工作节奏...")
    rhythm = engine.detect_work_rhythm(sample_conversations)
    print(f"深度工作时段: {rhythm['deep_work_hours']}")
    
    # 4. 生成预测
    print("\n[4] 生成预测...")
    
    # 时间预测
    time_predictions = engine.predict_by_time()
    print(f"时间预测: {len(time_predictions)} 个")
    for p in time_predictions[:2]:
        print(f"  - {p['predicted_need']} (置信度: {p['confidence']})")
    
    # 历史模式预测
    history_predictions = engine.predict_by_history()
    print(f"历史模式预测: {len(history_predictions)} 个")
    for p in history_predictions[:2]:
        print(f"  - {p['predicted_need']} (置信度: {p['confidence']})")
    
    # 5. 生成主动建议
    print("\n[5] 生成主动建议...")
    context = {"recent_emails": [{"unread": True}, {"unread": True}, {"unread": False}]}
    suggestions = engine.generate_suggestions(context)
    for i, s in enumerate(suggestions[:3], 1):
        print(f"  {i}. [{s['priority'].upper()}] {s['personalized_message']}")
    
    # 6. 保存用户模式
    engine.save_user_pattern()
    print("\n[6] 用户模式已保存")
    
    print("\n" + "=" * 50)
    print("演示完成!")
    print("=" * 50)


if __name__ == "__main__":
    demo()
