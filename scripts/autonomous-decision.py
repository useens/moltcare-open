#!/usr/bin/env python3
"""
自主决策执行引擎
基于规则的多步自动决策系统
"""

import json
import time
from datetime import datetime
from pathlib import Path

DECISIONS_FILE = Path("/root/.openclaw/workspace/decision-log.json")
RULES_FILE = Path("/root/.openclaw/workspace/decision-rules.json")

class AutonomousDecisionEngine:
    def __init__(self):
        self.decisions = []
        self.rules = {
            "storage_cleanup": {
                "trigger": {"metric": "disk_usage", "threshold": 80},
                "actions": ["cleanup_temp", "compress_logs", "archive_old"]
            },
            "git_sync": {
                "trigger": {"metric": "uncommitted_changes", "threshold": 10},
                "actions": ["git_add", "git_commit", "git_push"]
            },
            "restart_service": {
                "trigger": {"metric": "service_uptime", "threshold": 86400},
                "actions": ["check_health", "graceful_restart", "verify"]
            }
        }

    def evaluate_state(self, state):
        """评估当前状态并返回应执行的决策"""
        triggered_decisions = []

        for rule_name, rule in self.rules.items():
            trigger = rule["trigger"]
            metric = state.get(trigger["metric"])

            if metric is not None and metric >= trigger["threshold"]:
                triggered_decisions.append({
                    "rule": rule_name,
                    "timestamp": datetime.now().isoformat(),
                    "trigger_value": metric,
                    "actions": rule["actions"],
                    "status": "pending"
                })

        return triggered_decisions

    def execute_decision(self, decision):
        """执行决策（模拟）"""
        print(f"执行决策: {decision['rule']}")
        print(f"  触发值: {decision['trigger_value']}")
        print(f"  动作: {decision['actions']}")

        # 模拟执行
        for action in decision["actions"]:
            print(f"    → 执行: {action}")
            time.sleep(0.5)

        decision["status"] = "completed"
        decision["completed_at"] = datetime.now().isoformat()

        return decision

    def save_decision(self, decision):
        """保存决策记录"""
        self.decisions.append(decision)
        with open(DECISIONS_FILE, 'w') as f:
            json.dump(self.decisions, f, indent=2)

    def run(self, state):
        """运行决策引擎"""
        triggered = self.evaluate_state(state)

        if not triggered:
            print("当前状态无需执行决策")
            return []

        results = []
        for decision in triggered:
            result = self.execute_decision(decision)
            self.save_decision(result)
            results.append(result)

        return results

if __name__ == "__main__":
    # 测试用例
    engine = AutonomousDecisionEngine()

    test_states = [
        {"disk_usage": 85, "uncommitted_changes": 5},
        {"disk_usage": 75, "uncommitted_changes": 15},
        {"disk_usage": 90, "uncommitted_changes": 20},
    ]

    for state in test_states:
        print(f"\n{'='*60}")
        print(f"评估状态: {state}")
        engine.run(state)

    print(f"\n决策已保存到: {DECISIONS_FILE}")
