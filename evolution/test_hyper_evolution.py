#!/usr/bin/env python3
"""
Hyper-Evolution Engine - 简化演示版
运行：python test_hyper_evolution.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core import state, event_bus, StateManager
from collectors import run_all_collectors
from decider import decider
from executor import Executor

def main():
    print("🧬 Hyper-Evolution Engine - Demo")
    print("=" * 50)

    # 1. 收集数据
    print("\n📊 步骤 1: 收集系统数据...")
    run_all_collectors()
    print("✅ 数据收集完成")

    # 2. 评估
    print("\n🔍 步骤 2: 运行进化评估...")
    decision = decider.run_evaluation()
    if not decision:
        print("✅ 系统状态良好，无需进化")
        return

    print("📋 决策:")
    print(f"  触发条件: {decision['trigger']}")
    print(f"  置信度: {decision['confidence']:.0%}")
    print(f"  策略: {decision['strategy']}")

    # 3. 执行（dry-run）
    print("\n⚡ 步骤 3: 试运行执行...")
    executor = Executor()
    result = executor.execute(decision, dry_run=True)
    print(f"  结果: {'✅ 成功' if result.success else '❌ 失败'}")
    if result.errors:
        print(f"  错误: {result.errors}")

    print("\n✅ Demo 完成！")

if __name__ == "__main__":
    main()
