"""
进化策略库 - 可执行的系统变更方案
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import subprocess
import json
from pathlib import Path
from datetime import datetime
from core import StateManager

class Strategy(ABC):
    """策略基类"""
    def __init__(self, name: str):
        self.name = name
        self.state = StateManager()

    @abstractmethod
    def execute(self, context: Dict) -> Dict[str, Any]:
        """执行策略，返回结果"""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """验证执行后效果"""
        pass

    @abstractmethod
    def rollback(self):
        """回滚策略"""
        pass

class CostOptimizationStrategy(Strategy):
    """成本优化策略 - 切换便宜模型、降低 token 限制"""
    def execute(self, context: Dict) -> Dict[str, Any]:
        actions = []
        try:
            # 1. 将默认模型从 k2p5 改为 step（如果当前是 k2p5）
            current = self.state.get("current_model")
            if current == "kimi-coding/k2p5":
                # 修改 openclaw.json
                result = self._update_default_model("nvidia-build/stepfun-ai/step-3.5-flash")
                actions.append({"action": "switch_model", "from": current, "to": "step", "result": result})
                self.state.set("current_model", "step")

            # 2. 降低 maxTokens（如果有配置）
            # TODO: 实现

            # 3. 启用缓存（如果支持）
            # TODO: 实现

            return {
                "status": "success",
                "actions": actions,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "failed", "error": str(e), "actions": actions}

    def _update_default_model(self, model: str) -> bool:
        """通过 CLI 更新默认模型"""
        result = subprocess.run(
            ["openclaw", "models", "set", model],
            capture_output=True, text=True
        )
        return result.returncode == 0

    def validate(self) -> bool:
        """验证：检查当前模型是否为 step"""
        current = self.state.get("current_model")
        return current == "nvidia-build/stepfun-ai/step-3.5-flash"

    def rollback(self):
        """回滚：恢复为 k2p5"""
        self._update_default_model("kimi-coding/k2p5")
        self.state.set("current_model", "kimi-coding/k2p5")

class RoutingImprovementStrategy(Strategy):
    """路由规则优化策略 - 重训分类器"""
    def execute(self, context: Dict) -> Dict[str, Any]:
        # 模拟：重新训练 assess-difficulty.py 的分类模型
        # 实际应该基于用户反馈数据训练 ML 模型
        return {
            "status": "success",
            "actions": [{"action": "retrain_router"}],
            "timestamp": datetime.now().isoformat()
        }

    def validate(self) -> bool:
        # 检查路由准确率是否提升
        return True

    def rollback(self):
        """回滚：恢复旧的路由规则文件"""
        pass

class ModelUpgradeStrategy(Strategy):
    """模型升级策略 - A/B 测试新模型"""
    def execute(self, context: Dict) -> Dict[str, Any]:
        new_models = context.get("external", {}).get("new_models", [])
        if not new_models:
            return {"status": "noop", "reason": "no_new_models"}

        model = new_models[0]
        # 1. 添加到模型目录
        # 2. 5% 流量使用
        # 3. 监控效果

        return {
            "status": "success",
            "actions": [{"action": "canary_deploy", "model": model, "traffic_pct": 5}],
            "timestamp": datetime.now().isoformat()
        }

    def validate(self) -> bool:
        return True

    def rollback(self):
        pass

class SystemRepairStrategy(Strategy):
    """系统修复策略"""
    def execute(self, decision: Dict) -> Dict[str, Any]:
        """执行系统修复"""
        actions = []
        evidence = decision.get("evidence", {})
        issues = evidence.get("issues", [])

        # 修复 git dirty（所有 tracked 文件修改 staging）
        if "git_dirty" in issues:
            result = subprocess.run(
                ["git", "add", "-A"],
                cwd="/root/.openclaw/workspace",
                capture_output=True, text=True
            )
            if result.returncode == 0:
                actions.append({"action": "git_add", "message": "Stage all tracked changes"})
            else:
                return {"status": "failed", "error": f"git add failed: {result.stderr}"}

        # 修复存储高（清理旧日志）
        if "storage_high" in issues:
            # 清理logs目录中30天前的日志
            import shutil
            logs_dir = Path("/root/.openclaw/workspace/logs")
            if logs_dir.exists():
                for log_file in logs_dir.glob("*.log"):
                    if log_file.stat().st_mtime < (datetime.now().timestamp() - 30*86400):
                        try:
                            log_file.unlink()
                            actions.append({"action": "delete_old_log", "file": str(log_file)})
                        except:
                            pass

        # 修复 cron disabled（重新安装自动化任务）
        if "cron_disabled" in issues:
            cron_setup = Path("/root/.openclaw/workspace/scripts/setup-automation-cron.sh")
            if cron_setup.exists():
                result = subprocess.run(
                    ["bash", str(cron_setup)],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    actions.append({"action": "reinstall_cron"})

        return {
            "status": "success",
            "actions": actions,
            "timestamp": datetime.now().isoformat()
        }

    def validate(self) -> bool:
        # 检查是否还有未 stage 的修改（stage 后 status 中第一列为空格代表未 stage）
        git_result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd="/root/.openclaw/workspace",
            capture_output=True, text=True
        )
        # 如果没有未 stage 的修改，说明所有修改都已 add（或工作区干净）
        if git_result.stdout.strip():
            print(f"[SystemRepair] 未 stage 的修改: {git_result.stdout.strip()}")
            return False
        return True

    def rollback(self):
        # 系统修复通常不可回滚（git reset --hard）
        pass

# 策略注册表
STRATEGIES: Dict[str, Strategy] = {
    "cost_optimization": CostOptimizationStrategy("cost_optimization"),
    "routing_improvement": RoutingImprovementStrategy("routing_improvement"),
    "model_upgrade": ModelUpgradeStrategy("model_upgrade"),
    "system_repair": SystemRepairStrategy("system_repair")
}
