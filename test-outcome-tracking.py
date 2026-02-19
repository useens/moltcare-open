#!/usr/bin/env python3
"""测试决策效果追踪"""
import sys
import os
from pathlib import Path

# 添加路径
WORKSPACE = Path("/root/.openclaw/workspace")
SCRIPTS_DIR = WORKSPACE / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# 注意：autonomous-decision-engine.py 使用下划线和连字符混合命名
import importlib.util

spec = importlib.util.spec_from_file_location(
    "decision_engine",
    WORKSPACE / "scripts" / "autonomous-decision-engine.py"
)
decision_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision_engine)

DecisionEngine = decision_engine.DecisionEngine
DecisionContext = decision_engine.DecisionContext
DecisionType = decision_engine.DecisionType
RiskLevel = decision_engine.RiskLevel
from datetime import datetime

print("="*60)
print("🧪 测试完整决策效果追踪流程")
print("="*60)

# 创建引擎（禁用进化和Redis辩论以快速测试）
engine = DecisionEngine(enable_evolution=False)
engine.expert_panel.use_redis = False  # 禁用Redis辩论

# 创建一个测试决策上下文
context = DecisionContext(
    task_id=f'manual-test-{datetime.now().strftime("%Y%m%d%H%M%S")}',
    task_description='测试：验证决策效果追踪',
    decision_type=DecisionType.SYSTEM_MAINTENANCE,
    risk_level=RiskLevel.L3_STANDARD,
    source='manual_test',
    created_at=datetime.now()
)

# 处理决策
print(f"\n处理决策: {context.task_id}")
decision = engine.process_decision(context, execute_evolution=False)

print(f"\n✅ 决策完成:")
print(f"   ID: {decision.context.task_id}")
print(f"   类型: {decision.context.decision_type.value}")
print(f"   风险等级: {decision.context.risk_level.name}")
print(f"   执行批准: {decision.execution_approved}")

# 检查outcomes文件
outcomes_file = WORKSPACE / "data" / "decision-outcomes.jsonl"
print(f"\n📊 检查追踪文件: {outcomes_file}")

if outcomes_file.exists():
    with open(outcomes_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"   记录数: {len(lines)}")
    if lines:
        import json
        latest = json.loads(lines[-1])
        print(f"   最新记录: {latest['decision_id']}")
        print(f"   任务类型: {latest['task_type']}")
        print(f"   成功: {latest['success']}")
        print(f"   质量分: {latest['quality_score']}/10")
else:
    print("   ⚠️ 文件不存在")

print("\n" + "="*60)
print("测试完成！")
