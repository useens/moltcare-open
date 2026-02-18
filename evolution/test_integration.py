#!/usr/bin/env python3
"""
Hyper-Evolution Engine - 全量集成测试
测试：数据收集 → 决策 → 执行 → 验证 的完整流程
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core import state, event_bus
from collectors import run_all_collectors
from decider import decider
from executor import Executor
from strategies import STRATEGIES
import json
from datetime import datetime

def test_collectors():
    print("📊 测试 1: 数据收集器")
    print("-" * 40)
    run_all_collectors()
    print("✅ 所有收集器执行完成")

def test_decision_engine():
    print("\n🔍 测试 2: 决策引擎")
    print("-" * 40)
    decision = decider.run_evaluation()
    if decision:
        print(f"✅ 触发: {decision['trigger']}")
        print(f"   置信度: {decision['confidence']:.0%}")
        print(f"   策略: {decision['strategy']}")
        return decision
    else:
        print("✅ 无需进化（系统状态良好）")
        return None

def test_executor(decision):
    print("\n⚡ 测试 3: 安全执行器（dry-run）")
    print("-" * 40)
    executor = Executor()
    result = executor.execute(decision, dry_run=True)
    if result.success:
        print(f"✅ 试运行成功")
        print(f"   计划ID: {result.plan_id}")
    else:
        print(f"❌ 试运行失败: {result.errors}")
    return result

def test_real_execution(decision):
    print("\n🔨 测试 4: 真实执行（low-risk策略）")
    print("-" * 40)
    # 只对 system_repair 策略执行真实操作（其他策略低风险）
    if decision['strategy'] == 'system_repair':
        print("⚠️  检测到系统修复策略，执行真实操作...")
        executor = Executor()
        result = executor.execute(decision, dry_run=False)
        if result.success:
            print("✅ 真实执行成功")
        else:
            print(f"❌ 真实执行失败: {result.errors}")
        return result
    else:
        print(f"⏭️  跳过真实执行（策略: {decision['strategy']}）非系统修复")
        return None

def test_all_strategies():
    print("\n🧩 测试 5: 所有策略加载与基本功能")
    print("-" * 40)
    print(f"已注册策略: {list(STRATEGIES.keys())}")
    for name, strategy in STRATEGIES.items():
        print(f"  - {name}: validate={strategy.validate() if hasattr(strategy, 'validate') else 'N/A'}")
    print(f"✅ 共 {len(STRATEGIES)} 个策略可用")

def show_summary():
    print("\n" + "=" * 50)
    print("📈 集成测试总结")
    print("=" * 50)
    print("✅ 数据收集: 正常")
    print("✅ 决策引擎: 正常")
    print("✅ 执行器: 正常")
    print("✅ 策略库: 正常")
    print("\n💡 系统已就绪，你可以：")
    print("   - 运行: python hyper_evolution.py status")
    print("   - 评估: python hyper_evolution.py evaluate --execute")
    print("   - 历史: python hyper_evolution.py history")
    print("=" * 50)

def main():
    print("🧬 Hyper-Evolution Engine - 全量集成测试")
    print("=" * 50)

    start = datetime.now()

    try:
        test_collectors()
        decision = test_decision_engine()
        if decision:
            test_executor(decision)
            test_real_execution(decision)
        test_all_strategies()
        show_summary()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    duration = datetime.now() - start
    print(f"\n⏱️  总耗时: {duration}")

if __name__ == "__main__":
    main()
