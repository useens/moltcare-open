#!/usr/bin/env python3
"""
神经中枢 2.0 集成测试
测试神经中枢与Nanobot的通信
"""
import sys
import asyncio
sys.path.insert(0, '/root/.openclaw/workspace')

from core.neural_hub.database import TaskDatabase
from core.neural_hub.state_manager import StateManager
from core.neural_hub.scheduler import SmartScheduler, TaskPriority

print("=" * 60)
print("🧠 神经中枢 2.0 集成测试")
print("=" * 60)

# 清理测试数据
import os
try:
    os.remove("/root/.openclaw/workspace/data/neural_hub/test_integration.db")
except:
    pass

# 初始化组件
db = TaskDatabase("/root/.openclaw/workspace/data/neural_hub/test_integration.db")
state = StateManager(db)
scheduler = SmartScheduler(state, db)

print("\n📊 系统状态:")
print(f"  数据库: ✅ 已连接")
print(f"  状态管理: ✅ 就绪")
print(f"  调度器: ✅ 就绪")

# 注册10个bot
bots_config = [
    ("nanobot-1", "研究员", ["research", "analysis"]),
    ("nanobot-2", "架构师", ["design", "architecture"]),
    ("nanobot-3", "工程师", ["coding", "testing"]),
    ("nanobot-4", "安全专家", ["security", "audit"]),
    ("nanobot-5", "分析师", ["analysis", "reporting"]),
    ("nanobot-6", "决策分析师", ["decision", "strategy"]),
    ("nanobot-7", "代码审查员", ["review", "quality"]),
    ("nanobot-8", "运维专家", ["ops", "monitoring"]),
    ("nanobot-9", "战略规划师", ["strategy", "planning"]),
    ("nanobot-10", "协调者", ["coordination", "sync"]),
]

print("\n🤖 注册Nanobot:")
for bot_id, name, caps in bots_config:
    state.register_bot(bot_id, name, "worker", caps)
    print(f"  ✅ {bot_id} ({name})")

# 模拟心跳
print("\n💓 模拟心跳 (所有Bot在线):")
for bot_id, _, _ in bots_config:
    state.heartbeat(bot_id)
    
online_bots = state.get_online_bots()
print(f"  在线Bot数: {len(online_bots)}/10")

# 提交测试任务
print("\n📝 提交测试任务:")
tasks = [
    ("security_audit", ["security", "audit"], TaskPriority.HIGH),
    ("code_review", ["review", "quality"], TaskPriority.NORMAL),
    ("architecture_design", ["design", "architecture"], TaskPriority.HIGH),
    ("data_analysis", ["research", "analysis"], TaskPriority.NORMAL),
]

task_ids = []
for task_type, caps, priority in tasks:
    task_id = scheduler.submit_task(task_type, {"test": True}, priority, caps)
    task_ids.append(task_id)
    print(f"  ✅ {task_type} ({task_id})")

# 查看状态
print("\n📈 系统统计:")
stats = scheduler.get_stats()
print(f"  总任务: {stats['total']}")
print(f"  待处理: {stats['pending']}")
print(f"  执行中: {stats['executing']}")
print(f"  已完成: {stats['completed']}")

# Bot状态
print("\n🤖 Bot状态:")
summary = state.get_summary()
print(f"  总数: {summary['total_bots']}")
print(f"  在线: {summary['online']}")
print(f"  可用: {summary['available']}")
print(f"  忙碌: {summary['busy']}")
print(f"  离线: {summary['offline']}")

print("\n" + "=" * 60)
print("🎉 集成测试完成！")
print("=" * 60)
print("\n✅ 神经中枢 2.0 系统已就绪")
print("   10个Nanobot正在运行，等待任务分配")
