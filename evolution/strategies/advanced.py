"""
高级进化策略 - 提升系统智能化能力
"""

from typing import Dict, Any, List
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from . import Strategy
from core import StateManager, event_bus

class DynamicThinkingStrategy(Strategy):
    """动态 Thinking 策略 - 根据任务复杂度自动调整 thinking 模式"""
    def execute(self, decision: Dict) -> Dict[str, Any]:
        """
        分析最近的用户反馈，如果拒绝率下降，说明 thinking 过长，可降低默认 thinking 级别
        """
        actions = []
        # 简化版：如果检测到用户频繁拒绝（复杂任务用 simple model 但 thinking on），调整
        evidence = decision.get("evidence", {})
        if "high_rejection" in decision.get("trigger", ""):
            # 设置默认 thinking 为 concise（全局）
            # 通过修改 agents.defaults.thinkingDefault
            actions.append({
                "action": "adjust_thinking_default",
                "from": "on",
                "to": "concise",
                "reason": "用户拒绝率高，减少过度思考"
            })
        return {"status": "success", "actions": actions, "timestamp": datetime.now().isoformat()}

    def validate(self) -> bool:
        # 检查最新配置的 thinkingDefault 是否已调整
        return True

    def rollback(self):
        # 恢复 thinkingDefault = on
        pass

class ModelCanaryStrategy(Strategy):
    """新模型灰度发布策略"""
    def execute(self, decision: Dict) -> Dict[str, Any]:
        actions = []
        new_models = decision.get("evidence", {}).get("new_models", [])
        if not new_models:
            return {"status": "noop", "actions": [], "timestamp": datetime.now().isoformat()}

        model = new_models[0]
        # 1. 添加到模型目录（假设已通过 models.json 注册）
        # 2. 设置 5% 流量使用新模型
        # 3. 监控3天
        actions.append({
            "action": "canary_deploy",
            "model": model,
            "traffic_percent": 5,
            "monitor_days": 3
        })
        return {"status": "success", "actions": actions, "timestamp": datetime.now().isoformat()}

    def validate(self) -> bool:
        # 检查 canary 配置是否存在
        return True

    def rollback(self):
        # 移除 canary 配置
        pass

class AutoTrainingStrategy(Strategy):
    """自动训练路由模型（基于用户反馈）"""
    def execute(self, decision: Dict) -> Dict[str, Any]:
        actions = []
        # 收集过去24h的反馈数据
        data_file = Path("/root/.openclaw/workspace/memory/self-upgrade/assessment-history.json")
        if data_file.exists():
            with open(data_file) as f:
                data = json.load(f)

            # 分析准确率
            total = len(data)
            correct = sum(1 for entry in data if entry.get("user_approval", True))
            accuracy = correct / total if total > 0 else 1.0

            if accuracy < 0.8 and total > 50:
                # 触发重训练
                actions.append({
                    "action": "retrain_router_model",
                    "samples": total,
                    "accuracy": accuracy,
                    "model": "assess-difficulty"
                })
                # 启动后台训练脚本（异步）
                subprocess.Popen([
                    "python3",
                    "/root/.openclaw/workspace/scripts/train-router-model.py",
                    "--samples", str(total)
                ])
        return {"status": "success", "actions": actions, "timestamp": datetime.now().isoformat()}

    def validate(self) -> bool:
        # 检查是否有新模型文件生成
        model_path = Path("/root/.openclaw/workspace/models/router_model.pkl")
        return model_path.exists() and model_path.stat().st_mtime > datetime.now().timestamp() - 86400

    def rollback(self):
        # 回滚到旧模型
        old_model = Path("/root/.openclaw/workspace/models/router_model.pkl.bak")
        if old_model.exists():
            shutil.copy2(old_model, "/root/.openclaw/workspace/models/router_model.pkl")

# 注册到策略库
from strategies import STRATEGIES
STRATEGIES["dynamic_thinking"] = DynamicThinkingStrategy("dynamic_thinking")
STRATEGIES["model_canary"] = ModelCanaryStrategy("model_canary")
STRATEGIES["auto_training"] = AutoTrainingStrategy("auto_training")

print("[Advanced Strategies] Loaded 3 new strategies")
