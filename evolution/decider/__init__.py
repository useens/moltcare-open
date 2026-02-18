"""
决策引擎 - 评估数据并选择进化策略
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
from core import event_bus, StateManager

DB_PATH = Path("/root/.openclaw/workspace/evolution/data/evolution.db")

class Trigger:
    """触发条件基类"""
    def __init__(self, name: str, confidence_threshold: float = 0.8):
        self.name = name
        self.threshold = confidence_threshold

    def check(self, context: Dict) -> Optional[Dict]:
        """检查是否触发，返回决策或None"""
        raise NotImplementedError

class CostSpikeTrigger(Trigger):
    """成本飙升触发"""
    def check(self, context: Dict) -> Optional[Dict]:
        perf = context.get("performance", {})
        costs = perf.get("costs", {})
        # 模拟：检查成本增长率
        # 实际应从数据库对比过去6小时 vs 前6小时
        cost_spike = False  # TODO: 实现真实检测
        if cost_spike:
            return {
                "trigger": "cost_spike",
                "confidence": 0.9,
                "evidence": {"cost_increase_pct": 35},
                "strategy": "cost_optimization"
            }
        return None

class AccuracyDropTrigger(Trigger):
    """路由准确率下降触发"""
    def check(self, context: Dict) -> Optional[Dict]:
        behavior = context.get("behavior", {})
        accuracy = behavior.get("routing_accuracy", {}).get("accuracy_rate", 1.0)
        if accuracy < 0.85:
            return {
                "trigger": "accuracy_drop",
                "confidence": 0.85,
                "evidence": {"accuracy": accuracy},
                "strategy": "routing_improvement"
            }
        return None

class UserRejectionTrigger(Trigger):
    """用户拒绝率过高触发"""
    def check(self, context: Dict) -> Optional[Dict]:
        behavior = context.get("behavior", {})
        feedback = behavior.get("user_feedback", {})
        total = feedback.get("approvals", 0) + feedback.get("rejections", 0)
        if total > 50:
            rejection_rate = feedback.get("rejections", 0) / total if total > 0 else 0
            if rejection_rate > 0.15:
                return {
                    "trigger": "high_rejection",
                    "confidence": 0.8,
                    "evidence": {"rejection_rate": rejection_rate},
                    "strategy": "routing_improvement"
                }
        return None

class NewModelTrigger(Trigger):
    """新模型可用触发"""
    def check(self, context: Dict) -> Optional[Dict]:
        external = context.get("external", {})
        new_models = external.get("new_models", [])
        if new_models:
            return {
                "trigger": "new_model_available",
                "confidence": 0.95,
                "evidence": {"new_models": new_models},
                "strategy": "model_upgrade"
            }
        return None

class CriticalErrorTrigger(Trigger):
    """系统异常触发（如存储>80%、git dirty）"""
    def check(self, context: Dict) -> Optional[Dict]:
        system = context.get("system", {})
        issues = []

        storage_status = system.get("storage", {}).get("status")
        if storage_status != "healthy":
            issues.append("storage_high")

        git_status = system.get("git", {}).get("status")
        if git_status != "healthy":
            issues.append("git_dirty")

        cron_status = system.get("cron", {}).get("enabled", False)
        if not cron_status:
            issues.append("cron_disabled")

        if issues:
            return {
                "trigger": "system_issue",
                "confidence": 0.99,
                "evidence": {"issues": issues},
                "strategy": "system_repair"
            }
        return None

class FeedbackBasedTrigger(Trigger):
    """基于用户反馈的触发（为高级策略提供信号）"""
    def check(self, context: Dict) -> Optional[Dict]:
        behavior = context.get("behavior", {})
        feedback = behavior.get("user_feedback", {})
        total = feedback.get("approvals", 0) + feedback.get("rejections", 0)

        if total < 100:
            return None  # 数据不足

        rejection_rate = feedback.get("rejections", 0) / total
        if rejection_rate > 0.2:
            return {
                "trigger": "high_rejection_rate",
                "confidence": 0.85,
                "evidence": {"rejection_rate": rejection_rate, "samples": total},
                "strategy": "dynamic_thinking"
            }

        # 检查路由准确率
        accuracy = behavior.get("routing_accuracy", {}).get("accuracy_rate", 1.0)
        if accuracy < 0.75:
            return {
                "trigger": "low_routing_accuracy",
                "confidence": 0.8,
                "evidence": {"accuracy": accuracy, "samples": total},
                "strategy": "auto_training"
            }

        return None

class DecisionEngine:
    """决策引擎 - 综合所有触发器"""
    def __init__(self):
        self.state = StateManager()
        self.triggers: List[Trigger] = [
            CostSpikeTrigger("cost_spike"),
            AccuracyDropTrigger("accuracy_drop"),
            UserRejectionTrigger("high_rejection"),
            FeedbackBasedTrigger("feedback_based"),  # 新增
            NewModelTrigger("new_model"),
            CriticalErrorTrigger("system_issue")
        ]
        self.event_bus = event_bus
        self.event_bus.subscribe("data.collected", self.on_data_collected)

    def on_data_collected(self, event):
        """收到数据收集事件时触发评估"""
        self.evaluate(event.data)

    def evaluate(self, context: Dict) -> Optional[Dict]:
        """评估所有触发条件"""
        decisions = []
        for trigger in self.triggers:
            decision = trigger.check(context)
            if decision:
                decisions.append(decision)

        if not decisions:
            return None

        # 选择置信度最高的决策
        decisions.sort(key=lambda d: d["confidence"], reverse=True)
        best = decisions[0]

        # 检查是否超过阈值
        if best["confidence"] >= self.state.get("config", {}).get("confidence_threshold", 0.8):
            best["status"] = "proposed"
            best["timestamp"] = datetime.now().isoformat()
            return best

        return None

    def run_evaluation(self) -> Optional[Dict]:
        """手动运行一次完整评估"""
        # 从数据库获取最新数据
        context = self._load_latest_context()
        return self.evaluate(context)

    def _load_latest_context(self) -> Dict:
        """从数据库加载最新上下文"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        context = {}
        for collector_name in ["performance", "behavior", "system", "external"]:
            cursor.execute("""
                SELECT data FROM metrics
                WHERE collector = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (collector_name,))
            row = cursor.fetchone()
            if row:
                import json
                context[collector_name] = json.loads(row["data"])

        conn.close()
        return context

# 全局实例
decider = DecisionEngine()

if __name__ == "__main__":
    decision = decider.run_evaluation()
    if decision:
        print(json.dumps(decision, indent=2, ensure_ascii=False))
    else:
        print("✅ 无需进化")  # No evolution needed
