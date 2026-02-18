"""
执行器 - 安全执行进化策略（沙箱验证 + 渐进部署 + 自动回滚）
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any
from core import StateManager, event_bus, Event
from collectors import DB_PATH  # 导入数据库路径

SANDBOX_DIR = Path("/root/.openclaw/workspace/evolution/sandbox")
BACKUP_DIR = Path("/root/.openclaw/workspace/evolution/backups")

class ExecutionPlan:
    """执行计划"""
    def __init__(self, strategy_name: str, actions: List[Dict], context: Dict):
        self.strategy = strategy_name
        self.actions = actions
        self.context = context
        self.id = f"{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.status = "pending"
        self.backup_path = None

class ExecutionResult:
    """执行结果"""
    def __init__(self, plan: ExecutionPlan, success: bool, errors: List = None):
        self.plan_id = plan.id
        self.strategy = plan.strategy
        self.success = success
        self.errors = errors or []
        self.timestamp = datetime.now().isoformat()

class SandboxTester:
    """沙箱测试器"""
    def __init__(self):
        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    def test_plan(self, plan: ExecutionPlan) -> bool:
        """在执行真实系统前，在沙箱中测试"""
        print(f"[Sandbox] Testing plan {plan.id}...")

        # 复制当前配置到沙箱
        config_src = Path("/root/.openclaw/openclaw.json")
        config_dst = SANDBOX_DIR / "openclaw.json"
        shutil.copy2(config_src, config_dst)

        # 模拟执行每个 action（不实际影响主系统）
        try:
            for action in plan.actions:
                action_type = action.get("action")
                if action_type == "switch_model":
                    # 修改沙箱配置中的模型
                    self._update_sandbox_model(config_dst, action["to"])
                # 其他 action...
            return True
        except Exception as e:
            print(f"[Sandbox] Test failed: {e}")
            return False

    def _update_sandbox_model(self, config_path: Path, model: str):
        """更新沙箱中的默认模型"""
        with open(config_path) as f:
            config = json.load(f)
        config["agents"]["defaults"]["model"]["primary"] = model
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

class Executor:
    """主执行器"""
    def __init__(self):
        self.state = StateManager()
        self.sandbox = SandboxTester()
        self.backup_retention = 10  # 保留10个备份
        self.event_bus = event_bus

    def execute(self, decision: Dict, dry_run: bool = False) -> ExecutionResult:
        """执行进化决策"""

        # 1. 生成执行计划
        from strategies import STRATEGIES
        strategy = STRATEGIES.get(decision["strategy"])
        if not strategy:
            return ExecutionResult(None, False, [f"Unknown strategy: {decision['strategy']}"])

        plan = ExecutionPlan(
            strategy_name=strategy.name,
            actions=[],  # strategy.execute 会填充
            context=decision
        )

        print(f"[Executor] Executing strategy: {strategy.name}")
        print(f"[Executor] Confidence: {decision.get('confidence')}")

        # 2. 创建备份（仅真实执行）
        if not dry_run:
            backup_ok = self._create_backup(plan)
            if not backup_ok:
                return ExecutionResult(plan, False, ["Backup failed"])

        # 3. 沙箱测试
        test_ok = self.sandbox.test_plan(plan)
        if not test_ok:
            return ExecutionResult(plan, False, ["Sandbox test failed"])

        # 4. 执行策略（仅真实执行）
        if not dry_run:
            try:
                result = strategy.execute(decision)  # 传递完整 decision（包含 evidence）
                plan.actions = result.get("actions", [])
                plan.status = "executed"
            except Exception as e:
                return ExecutionResult(plan, False, [str(e)])

            # 5. 验证（仅真实执行）
            if strategy.validate():
                plan.status = "validated"
                print(f"[Executor] ✅ Validation passed")
            else:
                # 自动回滚
                print(f"[Executor] ❌ Validation failed, rolling back...")
                self._rollback(plan)
                plan.status = "rolled_back"
                return ExecutionResult(plan, False, ["Validation failed, rolled back"])

            # 6. 记录结果
            self._record_decision(decision, plan, "success")
            event_bus.publish(Event(
                type="evolution.completed",
                source="Executor",
                timestamp=datetime.now(),
                data={"plan": plan.id, "status": plan.status}
            ))
        else:
            # dry-run 只记录计划，不执行
            plan.status = "dry_run"
            print("[Executor] ⏸️  Dry run mode - no changes applied")

        return ExecutionResult(plan, True)

    def _create_backup(self, plan: ExecutionPlan) -> bool:
        """创建配置备份"""
        try:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup_path = BACKUP_DIR / f"backup_{plan.id}.json"
            shutil.copy2("/root/.openclaw/openclaw.json", backup_path)
            plan.backup_path = str(backup_path)
            print(f"[Executor] Backup created: {backup_path}")
            return True
        except Exception as e:
            print(f"[Executor] Backup failed: {e}")
            return False

    def _rollback(self, plan: ExecutionPlan):
        """回滚到备份"""
        if plan.backup_path and Path(plan.backup_path).exists():
            shutil.copy2(plan.backup_path, "/root/.openclaw/openclaw.json")
            print(f"[Executor] Rolled back to {plan.backup_path}")

            # 重启网关
            subprocess.run(["openclaw", "gateway", "restart"], capture_output=True)

    def _record_decision(self, decision: Dict, plan: ExecutionPlan, status: str):
        """记录决策到数据库"""
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO decisions (timestamp, trigger, strategy, confidence, action, status, before_state, after_state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            decision.get("trigger"),
            plan.strategy,
            decision.get("confidence"),
            json.dumps(plan.actions),
            status,
            json.dumps(decision),
            json.dumps({"current_model": self.state.get("current_model")})
        ))
        conn.commit()
        conn.close()

def main():
    """CLI entry point"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Evolution Executor")
    parser.add_argument("--decision", help="Decision JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Test without applying")
    args = parser.parse_args()

    if args.decision:
        with open(args.decision) as f:
            decision = json.load(f)
    else:
        # 从 decider 获取最新决策
        from decider import decider
        decision = decider.run_evaluation()
        if not decision:
            print("✅ No evolution needed")
            return

    executor = Executor()
    result = executor.execute(decision, dry_run=args.dry_run)

    print(json.dumps({
        "plan_id": result.plan_id,
        "success": result.success,
        "errors": result.errors,
        "timestamp": result.timestamp
    }, indent=2))

if __name__ == "__main__":
    main()
