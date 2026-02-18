#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from decider import decider
from executor import Executor, ExecutionPlan
from strategies import STRATEGIES

print("🔍 完整执行流程调试")

decision = decider.run_evaluation()
if not decision:
    print("No decision")
    sys.exit(0)

executor = Executor()
strategy = STRATEGIES[decision["strategy"]]
plan = ExecutionPlan(
    strategy_name=strategy.name,
    actions=[],
    context=decision
)

print(f"Plan: {plan.id}")

# 1. 备份（干运行=False）
print("\n1. 创建备份...")
try:
    backup_ok = executor._create_backup(plan)
    print(f"   Backup: {backup_ok}")
except Exception as e:
    print(f"   Backup error: {e}")

# 2. 沙箱测试
print("\n2. 沙箱测试...")
try:
    test_ok = executor.sandbox.test_plan(plan)
    print(f"   Test: {test_ok}")
except Exception as e:
    print(f"   Sandbox error: {e}")

# 3. 执行策略
print("\n3. 执行策略...")
try:
    result = strategy.execute(decision.get("context", {}))
    plan.actions = result.get("actions", [])
    plan.status = "executed"
    print(f"   Execute: OK, actions={plan.actions}")
except Exception as e:
    print(f"   Execute error: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# 4. 验证
print("\n4. 验证...")
try:
    valid = strategy.validate()
    print(f"   Validate: {valid}")
except Exception as e:
    print(f"   Validate error: {e}")

print("\n✅ 流程结束")
