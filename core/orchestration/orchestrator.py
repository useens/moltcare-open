"""
主-子代理协调系统集成模块
提供统一的 API 供主代理调用
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable, Set, Union
from datetime import datetime
import logging

from .task_queue import (
    TaskQueue, Task, TaskPriority, TaskStatus, TaskResult
)
from .agent_coordinator import (
    AgentCoordinator, SubAgent, AgentStatus, AgentCapability
)
from .result_aggregator import (
    ResultAggregator, AggregationStrategy, AggregationContext, 
    ResultItem, AggregationResult
)

logger = logging.getLogger(__name__)


@dataclass
class SubTaskRequest:
    """子任务请求"""
    name: str
    payload: Any
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: float = 300.0
    max_retries: int = 3
    required_capabilities: Optional[Set[AgentCapability]] = None
    expected_result_format: Optional[str] = None
    aggregation_strategy: AggregationStrategy = AggregationStrategy.SMART_MERGE


@dataclass
class OrchestratedResult:
    """协调执行结果"""
    success: bool
    content: Any
    task_id: str
    agent_id: Optional[str] = None
    execution_time_ms: float = 0.0
    retry_count: int = 0
    aggregation_info: Optional[AggregationResult] = None
    error: Optional[str] = None


class Orchestrator:
    """
    主-子代理协调器
    整合任务队列、代理协调和结果聚合
    """
    
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        heartbeat_interval: float = 30.0,
        enable_aggregation: bool = True
    ):
        self.task_queue = TaskQueue(max_concurrent=max_concurrent_tasks)
        self.agent_coordinator = AgentCoordinator(heartbeat_interval=heartbeat_interval)
        self.result_aggregator = ResultAggregator() if enable_aggregation else None
        self.enable_aggregation = enable_aggregation
        
        self._task_handlers: Dict[str, Callable] = {}
        self._running = False
        
    async def start(self):
        """启动协调器"""
        await self.task_queue.start()
        await self.agent_coordinator.start()
        self._running = True
        logger.info("Orchestrator started")
    
    async def stop(self, wait_for_pending: bool = True):
        """停止协调器"""
        self._running = False
        await self.task_queue.stop(wait_for_pending=wait_for_pending)
        await self.agent_coordinator.stop()
        logger.info("Orchestrator stopped")
    
    def register_task_handler(self, task_name: str, handler: Callable):
        """注册任务处理器"""
        self._task_handlers[task_name] = handler
        self.task_queue.register_handler(task_name, handler)
    
    async def spawn_subagent(
        self,
        name: str,
        capabilities: Set[AgentCapability],
        max_tasks: int = 5,
        priority: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SubAgent:
        """
        创建新的子代理
        """
        agent = await self.agent_coordinator.register_agent(
            name=name,
            capabilities=capabilities,
            max_tasks=max_tasks,
            priority=priority,
            metadata=metadata
        )
        return agent
    
    async def submit_task(
        self,
        request: SubTaskRequest,
        wait_for_completion: bool = True
    ) -> Union[Task, OrchestratedResult]:
        """
        提交子任务
        """
        # 1. 提交到任务队列
        task = await self.task_queue.submit(
            name=request.name,
            payload=request.payload,
            priority=request.priority,
            timeout=request.timeout,
            max_retries=request.max_retries
        )
        
        if not wait_for_completion:
            return task
        
        # 2. 等待完成
        completed_task = await self.task_queue.wait_for_task(
            task.task_id,
            timeout=request.timeout + 60  # 额外缓冲时间
        )
        
        if not completed_task:
            return OrchestratedResult(
                success=False,
                content=None,
                task_id=task.task_id,
                error="Task timeout or not found"
            )
        
        # 3. 构建结果
        success = completed_task.status == TaskStatus.COMPLETED
        execution_time = 0
        if completed_task.started_at and completed_task.completed_at:
            execution_time = (completed_task.completed_at - completed_task.started_at).total_seconds() * 1000
        
        return OrchestratedResult(
            success=success,
            content=completed_task.result,
            task_id=task.task_id,
            execution_time_ms=execution_time,
            retry_count=completed_task.retry_count,
            error=completed_task.error
        )
    
    async def submit_parallel(
        self,
        requests: List[SubTaskRequest],
        aggregate_results: bool = True,
        aggregation_strategy: Optional[AggregationStrategy] = None
    ) -> OrchestratedResult:
        """
        并行提交多个子任务
        支持结果聚合
        """
        if not requests:
            return OrchestratedResult(
                success=False,
                content=None,
                task_id="",
                error="No tasks provided"
            )
        
        # 提交所有任务（不等待）
        tasks = []
        for request in requests:
            task = await self.task_queue.submit(
                name=request.name,
                payload=request.payload,
                priority=request.priority,
                timeout=request.timeout,
                max_retries=request.max_retries
            )
            tasks.append((task, request))
        
        # 等待所有任务完成
        results = []
        result_items = []
        
        for task, request in tasks:
            completed = await self.task_queue.wait_for_task(
                task.task_id,
                timeout=request.timeout + 60
            )
            
            if completed:
                results.append(completed)
                
                # 创建结果项用于聚合
                success = completed.status == TaskStatus.COMPLETED
                result_items.append(ResultItem(
                    source=task.task_id,
                    content=completed.result,
                    confidence=1.0 if success else 0.0,
                    metadata={
                        'task_name': request.name,
                        'retry_count': completed.retry_count,
                        'error': completed.error
                    }
                ))
        
        # 聚合结果
        if aggregate_results and self.result_aggregator and len(result_items) > 1:
            strategy = aggregation_strategy or requests[0].aggregation_strategy
            context = AggregationContext(
                task_id=f"aggregate_{datetime.now().timestamp()}",
                strategy=strategy,
                expected_format=requests[0].expected_result_format
            )
            
            aggregation = await self.result_aggregator.aggregate(result_items, context)
            
            return OrchestratedResult(
                success=aggregation.success,
                content=aggregation.content,
                task_id=f"parallel_{len(tasks)}_tasks",
                execution_time_ms=aggregation.processing_time_ms,
                aggregation_info=aggregation
            )
        
        # 简单返回结果列表
        return OrchestratedResult(
            success=all(r.status == TaskStatus.COMPLETED for r in results),
            content=[r.result for r in results],
            task_id=f"parallel_{len(tasks)}_tasks"
        )
    
    async def submit_with_failover(
        self,
        request: SubTaskRequest,
        fallback_agents: Optional[List[str]] = None
    ) -> OrchestratedResult:
        """
        提交任务并支持故障转移
        """
        # 查找可用代理
        if request.required_capabilities:
            candidates = await self.agent_coordinator.get_agents_by_capability(
                list(request.required_capabilities)[0]
            )
        else:
            candidates = self.agent_coordinator.get_all_agents()
        
        # 按优先级排序
        candidates.sort(key=lambda a: (a.priority, -a.metrics.success_rate))
        
        # 尝试每个代理
        for agent in candidates:
            if not agent.is_available():
                continue
            
            # 分配任务
            assignment = await self.agent_coordinator.assign_task(
                task_id=f"failover_{datetime.now().timestamp()}",
                required_capabilities=request.required_capabilities or set(),
                preferred_agent=agent.agent_id
            )
            
            if not assignment:
                continue
            
            # 提交任务
            task = await self.task_queue.submit(
                name=request.name,
                payload=request.payload,
                priority=request.priority,
                timeout=request.timeout,
                max_retries=request.max_retries
            )
            
            # 等待完成
            completed = await self.task_queue.wait_for_task(
                task.task_id,
                timeout=request.timeout + 60
            )
            
            # 释放代理
            success = completed and completed.status == TaskStatus.COMPLETED
            await self.agent_coordinator.release_task(task.task_id, success=success)
            
            if success:
                execution_time = 0
                if completed.started_at and completed.completed_at:
                    execution_time = (completed.completed_at - completed.started_at).total_seconds() * 1000
                
                return OrchestratedResult(
                    success=True,
                    content=completed.result,
                    task_id=task.task_id,
                    agent_id=agent.agent_id,
                    execution_time_ms=execution_time
                )
            
            # 记录失败，尝试下一个
            logger.warning(f"Task failed on agent {agent.agent_id}, trying next...")
        
        return OrchestratedResult(
            success=False,
            content=None,
            task_id="",
            error="All agents failed or unavailable"
        )
    
    async def send_heartbeat(self, agent_id: str, metrics: Optional[Dict[str, Any]] = None):
        """发送代理心跳"""
        return await self.agent_coordinator.heartbeat(agent_id, metrics)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            'task_queue': self.task_queue.get_stats(),
            'agents': self.agent_coordinator.get_stats(),
            'running': self._running
        }
    
    async def graceful_shutdown(self, timeout: float = 60.0):
        """优雅关闭 - 等待所有任务完成"""
        logger.info(f"Initiating graceful shutdown with {timeout}s timeout...")
        
        # 停止接受新任务
        self._running = False
        
        # 等待队列清空
        await self.task_queue.wait_until_empty(timeout=timeout)
        
        # 停止所有组件
        await self.stop(wait_for_pending=False)
        
        logger.info("Graceful shutdown complete")


# 便捷函数：快速创建协调器
async def create_orchestrator(
    max_concurrent_tasks: int = 10,
    heartbeat_interval: float = 30.0
) -> Orchestrator:
    """创建并启动协调器"""
    orch = Orchestrator(
        max_concurrent_tasks=max_concurrent_tasks,
        heartbeat_interval=heartbeat_interval
    )
    await orch.start()
    return orch


# 便捷函数：快速提交任务
async def submit_subtask(
    orchestrator: Orchestrator,
    name: str,
    payload: Any,
    priority: TaskPriority = TaskPriority.NORMAL,
    timeout: float = 300.0
) -> OrchestratedResult:
    """快速提交单个子任务"""
    request = SubTaskRequest(
        name=name,
        payload=payload,
        priority=priority,
        timeout=timeout
    )
    return await orchestrator.submit_task(request, wait_for_completion=True)
