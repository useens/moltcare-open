#!/usr/bin/env python3
"""
神经中枢 2.0 集成测试
测试完整的工作流
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.neural_hub.database import TaskDatabase
from core.neural_hub.state_manager import StateManager
from core.neural_hub.scheduler import SmartScheduler, TaskPriority

print("=" * 60)
print("🧪 神经中枢 2.0 集成测试")
print("=" * 60)

# 清理测试数据
db = TaskDatabase()
state = StateManager(db)
scheduler = SmartScheduler(state, db)

# 测试 1: 注册10个bot
print("\n[1/5] 注册10个Nanobot...")
bots = [
    ("nanobot-1", "研究员", ["research", "analysis"]),
    ("nanobot-2", "架构师", ["design", "architecture"]),
    ("nanobot-3", "工程师", ["coding", "testing"]),
    ("nanobot-4", "安全专家", ["security", "audit"]),
    ("nanobot-5", "分析师", ["analysis", "reporting"]),
    ("nanobot-6", "决策分析师", ["decision", "strategy"]),
    ("nanobot-7", "代码审查员", ["code_review", "quality"]),
    ("nanobot-8", "运维专家", ["ops", "monitoring"]),
    ("nanobot-9", "战略规划师", ["strategy", "planning"]),
    ("nanobot-10", "协调者", ["coordination", "sync"]),
]

for bot_id, role, caps in bots:
    state.register_bot(bot_id, f"Bot-{bot_id}", role, caps)
    state.heartbeat(bot_id)

print(f"   ✅ 已注册 {len(bots)} 个bot")

# 测试 2: 智能任务分配
print("\n[2/5] 测试智能任务分配...")
tasks = [
    ("code_review", ["code_review"]),
    ("security_scan", ["security"]),
    ("analysis", ["analysis"]),
    ("architecture", ["architecture", "design"]),
]

for task_type, caps in tasks:
    bot = state.get_best_bot_for_task(caps)
    if bot:
        print(f"   ✅ {task_type} -> {bot.bot_id}")
    else:
        print(f"   ❌ {task_type} 无匹配bot")

# 测试 3: 提交任务
print("\n[3/5] 测试任务提交...")
task_ids = []
for i in range(5):
    task_id = scheduler.submit_task(
        f"task_type_{i}",
        {"index": i},
        TaskPriority.NORMAL,
        ["analysis"]
    )
    task_ids.append(task_id)

print(f"   ✅ 提交 {len(task_ids)} 个任务")

# 测试 4: 模拟任务执行流程
print("\n[4/5] 测试任务执行流程...")
for task_id in task_ids[:2]:
    task = scheduler.get_task_status(task_id)
    if task:
        # 模拟完成
        scheduler.complete_task(task_id, {"result": "success"})
        print(f"   ✅ 任务 {task_id[:8]}... 完成")

# 测试 5: 系统统计
print("\n[5/5] 系统统计...")
stats = {
    'bots': state.get_summary(),
    'tasks': scheduler.get_stats(),
}

print(f"   Bot统计: {stats['bots']}")
print(f"   任务统计: {stats['tasks']}")

print("\n" + "=" * 60)
print("🎉 集成测试完成！")
print("=" * 60)
print("\n系统已就绪，可以: ")
print("  1. 运行 ./scripts/deploy-neural-hub.sh 部署")
print("  2. 或在Python中导入 core.neural_hub 使用")
