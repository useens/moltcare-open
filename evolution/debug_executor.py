#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from decider import decider
from executor import Executor, ExecutionPlan

print("🔍 调试执行器")

# 获取决策
print("\n1. 获取决策...")
decision = decider.run_evaluation()
if not decision:
    print("没有决策，退出")
    sys.exit(0)

print("Decision:", decision)

# 创建执行器
print("\n2. 创建执行器...")
executor = Executor()
print("Executor created")

# 手动创建执行计划
print("\n3. 加载策略...")
from strategies import STRATEGIES
strategy = STRATEGIES.get(decision["strategy"])
print(f"Strategy: {strategy.name if strategy else None}")

if not strategy:
    print("未知策略，退出")
    sys.exit(1)

plan = ExecutionPlan(
    strategy_name=strategy.name,
    actions=[],
    context=decision
)
print(f"Plan ID: {plan.id}")

# 测试沙箱
print("\n4. 沙箱测试...")
try:
    test_ok = executor.sandbox.test_plan(plan)
    print(f"Sandbox test: {'OK' if test_ok else 'FAILED'}")
except Exception as e:
    print(f"Sandbox error: {e}")
    import traceback; traceback.print_exc()

print("\n✅ 调试完成")
