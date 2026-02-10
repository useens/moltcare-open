# 主-子代理协调系统使用指南

## 概述

主-子代理协调系统提供了以下核心能力：

1. **优先级任务队列** - 支持多种优先级、依赖管理、超时处理
2. **代理协调器** - 代理注册、心跳监控、负载均衡、故障转移
3. **结果聚合器** - 智能合并、冲突解决、质量评估

## 快速开始

```python
import asyncio
from core.orchestration import (
    Orchestrator, 
    SubTaskRequest, 
    TaskPriority,
    AgentCapability,
    create_orchestrator
)

async def main():
    # 1. 创建并启动协调器
    orchestrator = await create_orchestrator()
    
    # 2. 注册任务处理器
    async def my_task_handler(payload):
        # 处理任务
        return {"result": f"Processed: {payload}"}
    
    orchestrator.register_task_handler("my_task", my_task_handler)
    
    # 3. 提交任务
    request = SubTaskRequest(
        name="my_task",
        payload="some data",
        priority=TaskPriority.NORMAL,
        timeout=60.0
    )
    
    result = await orchestrator.submit_task(request)
    print(result.content)
    
    # 4. 关闭
    await orchestrator.stop()

asyncio.run(main())
```

## 核心组件

### 1. 任务队列 (TaskQueue)

```python
from core.orchestration import TaskQueue, TaskPriority

queue = TaskQueue(max_concurrent=5)
await queue.start()

# 提交任务
task = await queue.submit(
    name="task_name",
    payload={"data": "value"},
    priority=TaskPriority.HIGH,
    timeout=300.0,
    max_retries=3
)

# 等待完成
completed = await queue.wait_for_task(task.task_id)
```

**特性：**
- 优先级队列 (CRITICAL > HIGH > NORMAL > LOW > BACKGROUND)
- 自动超时处理
- 指数退避重试
- 任务依赖管理

### 2. 代理协调器 (AgentCoordinator)

```python
from core.orchestration import AgentCoordinator, AgentCapability

coordinator = AgentCoordinator()
await coordinator.start()

# 注册子代理
agent = await coordinator.register_agent(
    name="worker-1",
    capabilities={AgentCapability.CODE, AgentCapability.ANALYSIS},
    max_tasks=5
)

# 发送心跳
await coordinator.heartbeat(agent.agent_id, metrics={
    "cpu_usage": 30.0,
    "tasks_completed": 10
})

# 分配任务
assignment = await coordinator.assign_task(
    task_id="task-123",
    required_capabilities={AgentCapability.CODE}
)
```

**特性：**
- 代理注册与注销
- 心跳监控（自动检测无响应代理）
- 基于能力和负载的智能任务分配
- 自动故障转移

### 3. 结果聚合器 (ResultAggregator)

```python
from core.orchestration import (
    ResultAggregator, 
    AggregationStrategy,
    ResultItem,
    AggregationContext
)

aggregator = ResultAggregator()

# 准备结果
results = [
    ResultItem(source="agent1", content="Result A", confidence=0.9),
    ResultItem(source="agent2", content="Result B", confidence=0.8),
]

# 聚合
context = AggregationContext(
    task_id="task-123",
    strategy=AggregationStrategy.SMART_MERGE,
    deduplicate=True
)

result = await aggregator.aggregate(results, context)
```

**聚合策略：**
- `CONCATENATE` - 简单拼接
- `SMART_MERGE` - 智能合并（去重、排序）
- `VOTE` - 投票选择
- `CONSENSUS` - 共识算法
- `HIERARCHICAL` - 层级合并
- `SUMMARIZE` - 摘要汇总

## 高级用法

### 并行任务与聚合

```python
# 创建多个并行任务
requests = [
    SubTaskRequest(name="search", payload="query1"),
    SubTaskRequest(name="search", payload="query2"),
    SubTaskRequest(name="search", payload="query3"),
]

# 并行执行并聚合结果
result = await orchestrator.submit_parallel(
    requests,
    aggregate_results=True,
    aggregation_strategy=AggregationStrategy.SMART_MERGE
)
```

### 故障转移

```python
# 创建多个代理
agent1 = await orchestrator.spawn_subagent(
    name="primary",
    capabilities={AgentCapability.CODE},
    priority=1
)

agent2 = await orchestrator.spawn_subagent(
    name="backup",
    capabilities={AgentCapability.CODE},
    priority=2
)

# 提交带故障转移的任务
result = await orchestrator.submit_with_failover(
    request,
    fallback_agents=[agent1.agent_id, agent2.agent_id]
)
```

### 状态监控

```python
# 获取系统统计
stats = orchestrator.get_system_stats()
print(stats)
# {
#   'task_queue': {'pending': 2, 'running': 1, 'completed': 10},
#   'agents': {'total_agents': 3, 'active_tasks': 1},
#   'running': True
# }
```

## 最佳实践

1. **任务优先级**
   - 用户交互任务使用 `CRITICAL`
   - 常规任务使用 `NORMAL`
   - 后台任务使用 `BACKGROUND`

2. **代理能力**
   - 根据专长为代理分配合适的 `AgentCapability`
   - 定期检查代理健康状态

3. **结果聚合**
   - 对并行相似任务使用 `SMART_MERGE`
   - 对需要一致性的任务使用 `CONSENSUS`
   - 对大量结果使用 `SUMMARIZE`

4. **错误处理**
   - 设置合理的 `max_retries`（建议 2-3 次）
   - 使用 `timeout` 防止任务无限挂起
   - 为关键任务配置故障转移

## API 参考

### Orchestrator

| 方法 | 说明 |
|------|------|
| `start()` | 启动协调器 |
| `stop()` | 停止协调器 |
| `register_task_handler(name, handler)` | 注册任务处理器 |
| `spawn_subagent(...)` | 创建子代理 |
| `submit_task(request)` | 提交单任务 |
| `submit_parallel(requests)` | 提交并行任务 |
| `submit_with_failover(request)` | 带故障转移提交 |
| `send_heartbeat(agent_id)` | 发送心跳 |
| `get_system_stats()` | 获取系统统计 |

### TaskPriority

- `CRITICAL` (0) - 立即执行
- `HIGH` (1) - 高优先级
- `NORMAL` (2) - 普通优先级
- `LOW` (3) - 低优先级
- `BACKGROUND` (4) - 后台任务

### AgentCapability

- `CODE` - 代码相关
- `RESEARCH` - 研究搜索
- `WRITING` - 写作
- `ANALYSIS` - 分析
- `MEMORY` - 记忆管理
- `TOOLS` - 工具使用
- `BROWSER` - 浏览器控制
- `MULTIMODAL` - 多模态

## 示例代码

查看 `example.py` 获取完整示例：

```bash
cd /root/.openclaw/workspace
python -m core.orchestration.example
```
