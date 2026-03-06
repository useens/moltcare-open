#!/usr/bin/env python3
"""
神经中枢 2.0 基础设施测试
"""
import sys
import asyncio
import time
from pathlib import Path

# 添加路径
sys.path.insert(0, '/root/.openclaw/workspace')

# 直接导入核心组件，避免Redis依赖
sys.modules['aioredis'] = type(sys)('aioredis')  # Mock aioredis

from core.neural_hub.database import TaskDatabase
from core.neural_hub.state_manager import StateManager
from core.neural_hub.scheduler import SmartScheduler, TaskPriority

# 测试结果
results = []

def test(name):
    """测试装饰器"""
    def decorator(func):
        async def wrapper():
            try:
                print(f"\n🧪 测试: {name}")
                await func()
                results.append((name, True, None))
                print(f"   ✅ 通过")
                return True
            except Exception as e:
                results.append((name, False, str(e)))
                print(f"   ❌ 失败: {e}")
                return False
        return wrapper
    return decorator

# ========== 数据库测试 ==========

@test("数据库连接和初始化")
async def test_database_init():
    db = TaskDatabase("/root/.openclaw/workspace/data/neural_hub/test_tasks.db")
    # 测试是否创建成功
    stats = db.get_stats()
    assert 'tasks' in stats
    print(f"   数据库状态: {stats}")

@test("任务CRUD操作")
async def test_task_crud():
    db = TaskDatabase("/root/.openclaw/workspace/data/neural_hub/test_tasks.db")
    
    # 创建任务
    db.create_task("test-001", "analysis", 2, {"file": "test.py"})
    task = db.get_task("test-001")
    assert task is not None
    assert task['status'] == 'pending'
    print(f"   任务创建: {task['id']}")
    
    # 分配任务
    db.register_bot("bot-1", "测试Bot", "tester", ["analysis"])
    db.assign_task("test-001", "bot-1")
    task = db.get_task("test-001")
    assert task['status'] == 'assigned'
    print(f"   任务分配: {task['assigned_to']}")
    
    # 完成任务
    db.complete_task("test-001", {"result": "ok"})
    task = db.get_task("test-001")
    assert task['status'] == 'completed'
    print(f"   任务完成: {task['result']}")

# ========== 状态管理测试 ==========

@test("Bot注册和状态管理")
async def test_state_management():
    db = TaskDatabase("/root/.openclaw/workspace/data/neural_hub/test_tasks.db")
    state = StateManager(db)
    
    # 注册bot
    state.register_bot("nanobot-test", "测试员", "tester", ["test", "debug"])
    bot = state.get_bot("nanobot-test")
    assert bot is not None
    assert bot.name == "测试员"
    print(f"   Bot注册: {bot.name} ({bot.role})")
    
    # 更新状态
    state.update_state("nanobot-test", "busy", "task-001")
    bot = state.get_bot("nanobot-test")
    assert bot.state == "busy"
    print(f"   状态更新: {bot.state}")
    
    # 心跳
    state.heartbeat("nanobot-test")
    assert bot.is_online
    print(f"   心跳更新: 在线={bot.is_online}")

@test("Bot选择算法")
async def test_bot_selection():
    db = TaskDatabase("/root/.openclaw/workspace/data/neural_hub/test_tasks.db")
    state = StateManager(db)
    
    # 注册多个bot
    state.register_bot("bot-a", "Bot A", "engineer", ["coding"])
    state.register_bot("bot-b", "Bot B", "engineer", ["coding", "testing"])
    state.register_bot("bot-c", "Bot C", "analyst", ["analysis"])
    
    # 测试选择
    bot = state.get_best_bot_for_task(["coding"])
    assert bot is not None
    print(f"   选择Bot: {bot.bot_id} (能力匹配)")
    
    bot = state.get_best_bot_for_task(["coding", "testing"])
    assert bot is not None
    assert "testing" in bot.capabilities
    print(f"   选择Bot: {bot.bot_id} (双重能力匹配)")

# ========== 调度器测试 ==========

@test("调度器任务队列")
async def test_scheduler_queue():
    db = TaskDatabase("/root/.openclaw/workspace/data/neural_hub/test_tasks.db")
    state = StateManager(db)
    scheduler = SmartScheduler(state, db)
    
    # 注册可用的bot
    state.register_bot("worker-1", "工作者1", "worker", ["compute"])
    state.heartbeat("worker-1")  # 确保在线
    
    # 创建任务
    task_id = scheduler.submit_task(
        "compute",
        {"input": [1, 2, 3]},
        TaskPriority.NORMAL,
        ["compute"]
    )
    print(f"   任务提交: {task_id}")
    
    task = scheduler.get_task_status(task_id)
    assert task is not None
    assert task.status.value == 'pending'
    print(f"   任务状态: {task.status.value}")

@test("优先级队列排序")
async def test_priority_queue():
    db = TaskDatabase("/root/.openclaw/workspace/data/neural_hub/test_tasks.db")
    state = StateManager(db)
    scheduler = SmartScheduler(state, db)
    
    # 按不同优先级提交任务
    low_id = scheduler.submit_task("test", {}, TaskPriority.LOW)
    high_id = scheduler.submit_task("test", {}, TaskPriority.HIGH)
    normal_id = scheduler.submit_task("test", {}, TaskPriority.NORMAL)
    
    stats = scheduler.get_stats()
    assert stats['total'] >= 3
    print(f"   队列统计: {stats}")

# ========== 性能测试 ==========

@test("性能基准测试")
async def test_performance():
    db = TaskDatabase("/root/.openclaw/workspace/data/neural_hub/test_tasks.db")
    state = StateManager(db)
    
    # 注册100个bot
    start = time.time()
    for i in range(100):
        state.register_bot(f"perf-bot-{i}", f"Bot{i}", "worker", ["task"])
    reg_time = time.time() - start
    print(f"   注册100个Bot: {reg_time:.3f}s")
    
    # 查询状态
    start = time.time()
    for i in range(100):
        bot = state.get_bot(f"perf-bot-{i}")
    query_time = time.time() - start
    print(f"   查询100次: {query_time:.3f}s")
    
    # 创建100个任务
    scheduler = SmartScheduler(state, db)
    start = time.time()
    for i in range(100):
        scheduler.submit_task("perf_test", {"id": i})
    task_time = time.time() - start
    print(f"   创建100个任务: {task_time:.3f}s")
    
    assert reg_time < 1.0, "注册性能不达标"
    assert query_time < 0.5, "查询性能不达标"
    assert task_time < 1.0, "任务创建性能不达标"

# ========== 运行测试 ==========

async def run_tests():
    print("=" * 60)
    print("🧠 神经中枢 2.0 基础设施测试")
    print("=" * 60)
    
    # 清理测试数据库
    import os
    try:
        os.remove("/root/.openclaw/workspace/data/neural_hub/test_tasks.db")
    except:
        pass
    
    # 运行所有测试
    await test_database_init()
    await test_task_crud()
    await test_state_management()
    await test_bot_selection()
    await test_scheduler_queue()
    await test_priority_queue()
    await test_performance()
    
    # 报告结果
    print("\n" + "=" * 60)
    print("📊 测试报告")
    print("=" * 60)
    
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    
    for name, ok, error in results:
        status = "✅" if ok else "❌"
        print(f"{status} {name}")
        if error:
            print(f"   错误: {error}")
    
    print("\n" + "-" * 60)
    print(f"总计: {len(results)} 项 | 通过: {passed} | 失败: {failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！可以进入 Phase 3")
        return True
    else:
        print("\n⚠️ 部分测试失败，请修复后进入 Phase 3")
        return False

if __name__ == '__main__':
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
