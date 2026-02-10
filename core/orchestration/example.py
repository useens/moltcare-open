"""
主-子代理协调系统使用示例
演示如何创建代理、提交任务、处理结果
"""

import asyncio
import logging
from typing import Any

from core.orchestration import (
    Orchestrator,
    SubTaskRequest,
    TaskPriority,
    AgentCapability,
    AggregationStrategy,
    create_orchestrator,
    submit_subtask
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_task():
    """示例1: 基本任务提交"""
    print("\n=== 示例1: 基本任务提交 ===")
    
    orchestrator = await create_orchestrator()
    
    # 注册任务处理器
    async def process_data(payload: dict) -> dict:
        await asyncio.sleep(0.5)  # 模拟处理
        return {"processed": payload, "status": "success"}
    
    orchestrator.register_task_handler("process_data", process_data)
    
    # 提交任务
    request = SubTaskRequest(
        name="process_data",
        payload={"key": "value", "number": 42},
        priority=TaskPriority.NORMAL
    )
    
    result = await orchestrator.submit_task(request)
    print(f"Task completed: {result.success}")
    print(f"Result: {result.content}")
    
    await orchestrator.stop()


async def example_priority_queue():
    """示例2: 优先级队列"""
    print("\n=== 示例2: 优先级队列 ===")
    
    orchestrator = await create_orchestrator(max_concurrent_tasks=2)
    
    results = []
    
    async def slow_task(payload: dict) -> str:
        await asyncio.sleep(payload.get("delay", 1))
        return f"Task {payload['name']} completed"
    
    orchestrator.register_task_handler("slow_task", slow_task)
    
    # 提交不同优先级的任务
    tasks = [
        ("low_task", TaskPriority.LOW, 0.5),
        ("critical_task", TaskPriority.CRITICAL, 0.1),
        ("normal_task", TaskPriority.NORMAL, 0.3),
        ("high_task", TaskPriority.HIGH, 0.2),
    ]
    
    for name, priority, delay in tasks:
        request = SubTaskRequest(
            name="slow_task",
            payload={"name": name, "delay": delay},
            priority=priority
        )
        task = await orchestrator.submit_task(request, wait_for_completion=False)
        results.append((name, task))
    
    # 等待所有任务
    for name, task in results:
        completed = await orchestrator.task_queue.wait_for_task(task.task_id)
        print(f"{name}: {completed.status.name if completed else 'Unknown'}")
    
    await orchestrator.stop()


async def example_heartbeat():
    """示例3: 代理心跳机制"""
    print("\n=== 示例3: 代理心跳机制 ===")
    
    orchestrator = await create_orchestrator()
    
    # 创建子代理
    agent = await orchestrator.spawn_subagent(
        name="worker-1",
        capabilities={AgentCapability.CODE, AgentCapability.ANALYSIS},
        max_tasks=3
    )
    print(f"Agent created: {agent.agent_id}")
    
    # 模拟心跳
    for i in range(3):
        await orchestrator.send_heartbeat(
            agent.agent_id,
            metrics={
                "tasks_completed": i,
                "cpu_usage": 30 + i * 10,
                "memory_usage_mb": 100 + i * 20
            }
        )
        print(f"Heartbeat {i+1} sent")
        await asyncio.sleep(0.5)
    
    # 获取代理状态
    agent_info = await orchestrator.agent_coordinator.get_agent(agent.agent_id)
    print(f"Agent status: {agent_info.status.name}")
    print(f"Agent metrics: {agent_info.metrics}")
    
    await orchestrator.stop()


async def example_parallel_with_aggregation():
    """示例4: 并行任务与结果聚合"""
    print("\n=== 示例4: 并行任务与结果聚合 ===")
    
    orchestrator = await create_orchestrator()
    
    async def search_task(query: str) -> dict:
        """模拟搜索任务"""
        await asyncio.sleep(0.3)
        results = {
            "python": ["Python官网", "Python教程", "Python文档"],
            "async": ["AsyncIO指南", "异步编程", "Python并发"],
        }
        return {
            "query": query,
            "results": results.get(query, [f"Result for {query}"])
        }
    
    orchestrator.register_task_handler("search", search_task)
    
    # 提交并行搜索任务
    requests = [
        SubTaskRequest(
            name="search",
            payload="python",
            aggregation_strategy=AggregationStrategy.SMART_MERGE
        ),
        SubTaskRequest(
            name="search",
            payload="async",
            aggregation_strategy=AggregationStrategy.SMART_MERGE
        ),
        SubTaskRequest(
            name="search",
            payload="python",  # 重复查询，测试去重
            aggregation_strategy=AggregationStrategy.SMART_MERGE
        ),
    ]
    
    result = await orchestrator.submit_parallel(
        requests,
        aggregate_results=True,
        aggregation_strategy=AggregationStrategy.SMART_MERGE
    )
    
    print(f"Parallel tasks completed: {result.success}")
    print(f"Aggregated content: {result.content}")
    if result.aggregation_info:
        print(f"Sources: {result.aggregation_info.sources}")
        print(f"Confidence: {result.aggregation_info.confidence}")
    
    await orchestrator.stop()


async def example_retry_and_degradation():
    """示例5: 自动重试与降级"""
    print("\n=== 示例5: 自动重试与降级 ===")
    
    orchestrator = await create_orchestrator()
    
    attempt_count = 0
    
    async def flaky_task(payload: dict) -> str:
        nonlocal attempt_count
        attempt_count += 1
        
        # 前两次失败，第三次成功
        if attempt_count < 3:
            raise Exception(f"Simulated failure #{attempt_count}")
        
        return f"Success after {attempt_count} attempts"
    
    orchestrator.register_task_handler("flaky_task", flaky_task)
    
    request = SubTaskRequest(
        name="flaky_task",
        payload={},
        max_retries=3,  # 允许3次重试
        priority=TaskPriority.HIGH
    )
    
    result = await orchestrator.submit_task(request)
    print(f"Task success: {result.success}")
    print(f"Content: {result.content}")
    print(f"Retry count: {result.retry_count}")
    
    await orchestrator.stop()


async def example_failover():
    """示例6: 故障转移"""
    print("\n=== 示例6: 故障转移 ===")
    
    orchestrator = await create_orchestrator()
    
    # 创建多个代理
    agent1 = await orchestrator.spawn_subagent(
        name="primary-worker",
        capabilities={AgentCapability.CODE},
        max_tasks=1,
        priority=1
    )
    
    agent2 = await orchestrator.spawn_subagent(
        name="backup-worker",
        capabilities={AgentCapability.CODE},
        max_tasks=1,
        priority=2
    )
    
    print(f"Created agents: {agent1.agent_id}, {agent2.agent_id}")
    
    # 获取统计
    stats = orchestrator.get_system_stats()
    print(f"System stats: {stats}")
    
    await orchestrator.stop()


async def main():
    """运行所有示例"""
    print("=" * 50)
    print("主-子代理协调系统示例")
    print("=" * 50)
    
    try:
        await example_basic_task()
        await example_priority_queue()
        await example_heartbeat()
        await example_parallel_with_aggregation()
        await example_retry_and_degradation()
        await example_failover()
        
        print("\n" + "=" * 50)
        print("所有示例完成！")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
