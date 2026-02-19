#!/usr/bin/env python3
"""查看并验证决策效果追踪数据"""
import json
from pathlib import Path
from datetime import datetime

OUTCOMES_FILE = Path("/root/.openclaw/workspace/data/decision-outcomes.jsonl")

print("="*70)
print("决策效果追踪数据验证")
print("="*70)

if not OUTCOMES_FILE.exists():
    print(f"⚠️ 文件不存在: {OUTCOMES_FILE}")
    exit(1)

# 读取所有记录
records = []
with open(OUTCOMES_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            records.append(json.loads(line))

print(f"\n📊 记录总数: {len(records)}")

# 统计信息
if records:
    task_types = {}
    risk_levels = {}
    success_count = sum(1 for r in records if r['success'])
    avg_quality = sum(r['quality_score'] for r in records if r.get('quality_score')) / len(records)

    for r in records:
        task_type = r.get('task_type', 'unknown')
        task_types[task_type] = task_types.get(task_type, 0) + 1

        risk = r.get('risk_level', 'unknown')
        risk_levels[risk] = risk_levels.get(risk, 0) + 1

    print(f"\n📈 成功率: {success_count}/{len(records)} ({success_count/len(records)*100:.1f}%)")
    print(f"⭐ 平均质量分: {avg_quality:.1f}/10")

    print(f"\n🏷️ 任务类型分布:")
    for t, count in sorted(task_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   {t}: {count}")

    print(f"\n⚠️ 风险等级分布:")
    for r, count in sorted(risk_levels.items(), key=lambda x: x[1], reverse=True):
        print(f"   {r}: {count}")

    print(f"\n📝 最新5条记录:")
    print("-" * 70)
    for r in records[-5:]:
        print(f"ID: {r['decision_id']}")
        print(f"  类型: {r['task_type']}")
        print(f"  风险: {r['risk_level']}")
        print(f"  成功: {r['success']}")
        print(f"  质量分: {r.get('quality_score', 'N/A')}/10")
        print(f"  耗时: {r.get('execution_time_ms', 0):.1f}ms")
        print(f"  时间: {r['timestamp'][:19]}")
        print(f"  预期: {r.get('expected_result', 'N/A')[:60]}...")
        print(f"  实际: {r.get('actual_result', 'N/A')[:60]}...")
        if r.get('notes'):
            print(f"  备注: {r['notes']}")
        print()

print("="*70)
print("✅ 决策效果追踪系统部署成功")
print("="*70)
print("\n可用的验证命令:")
print("  python3 /root/.openclaw/workspace/scripts/autonomous-decision-engine.py --test-outcomes")
print("  python3 /root/.openclaw/workspace/scripts/autonomous-decision-engine.py --cycle")
print("  cat /root/.openclaw/workspace/data/decision-outcomes.jsonl")
