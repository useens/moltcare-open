"""
代理协调器模块 - 子代理管理、心跳机制、负载均衡
"""

import uuid
import asyncio
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """代理状态"""
    INITIALIZING = auto()   # 初始化中
    AVAILABLE = auto()      # 可用
    BUSY = auto()           # 忙碌
    DEGRADED = auto()       # 降级（性能下降）
    UNRESPONSIVE = auto()   # 无响应
    OFFLINE = auto()        # 离线
    ERROR = auto()          # 错误状态


class AgentCapability(Enum):
    """代理能力类型"""
    CODE = "code"               # 代码相关
    RESEARCH = "research"       # 研究搜索
    WRITING = "writing"         # 写作
    ANALYSIS = "analysis"       # 分析
    MEMORY = "memory"           # 记忆管理
    TOOLS = "tools"             # 工具使用
    BROWSER = "browser"         # 浏览器控制
    MULTIMODAL = "multimodal"   # 多模态


@dataclass
class AgentMetrics:
    """代理性能指标"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    success_rate: float = 1.0
    last_heartbeat: Optional[datetime] = None
    heartbeat_latency_ms: float = 0.0
    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0
    queue_depth: int = 0
    
    def update_success_rate(self):
        """更新成功率"""
        total = self.tasks_completed + self.tasks_failed
        if total > 0:
            self.success_rate = self.tasks_completed / total


@dataclass
class SubAgent:
    """子代理定义"""
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "unnamed"
    status: AgentStatus = AgentStatus.INITIALIZING
    capabilities: Set[AgentCapability] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    heartbeat_interval: float = 30.0  # 心跳间隔秒数
    max_tasks: int = 5  # 最大并发任务数
    current_tasks: int = 0
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)
    failover_targets: List[str] = field(default_factory=list)  # 故障转移目标
    priority: int = 1  # 优先级（数字越小优先级越高）
    
    def is_available(self) -> bool:
        """检查代理是否可用"""
        return (
            self.status in (AgentStatus.AVAILABLE, AgentStatus.BUSY) 
            and self.current_tasks < self.max_tasks
        )
    
    def is_healthy(self) -> bool:
        """检查代理健康状态"""
        if self.status in (AgentStatus.OFFLINE, AgentStatus.ERROR):
            return False
        if self.metrics.success_rate < 0.5:
            return False
        return True


@dataclass
class TaskAssignment:
    """任务分配记录"""
    task_id: str
    agent_id: str
    assigned_at: datetime
    timeout_at: datetime
    priority: int = 1


class AgentCoordinator:
    """
    代理协调器
    管理子代理注册、心跳监控、任务分配、故障转移
    """
    
    def __init__(
        self,
        heartbeat_interval: float = 30.0,
        heartbeat_timeout: float = 90.0,
        health_check_interval: float = 60.0
    ):
        self._agents: Dict[str, SubAgent] = {}
        self._assignments: Dict[str, TaskAssignment] = {}  # task_id -> assignment
        self._capability_index: Dict[AgentCapability, List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_timeout = heartbeat_timeout
        self._health_check_interval = health_check_interval
        
        self._heartbeat_callbacks: List[Callable[[str, AgentMetrics], None]] = []
        self._status_callbacks: List[Callable[[str, AgentStatus, AgentStatus], None]] = []
        self._failover_callbacks: List[Callable[[str, str], None]] = []
        
        self._monitor_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    async def start(self):
        """启动协调器"""
        self._shutdown = False
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("AgentCoordinator started")
    
    async def stop(self):
        """停止协调器"""
        self._shutdown = True
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("AgentCoordinator stopped")
    
    async def register_agent(
        self,
        name: str,
        capabilities: Set[AgentCapability],
        max_tasks: int = 5,
        priority: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None
    ) -> SubAgent:
        """注册新代理"""
        agent = SubAgent(
            agent_id=agent_id or str(uuid.uuid4()),
            name=name,
            capabilities=capabilities,
            max_tasks=max_tasks,
            priority=priority,
            metadata=metadata or {},
            heartbeat_interval=self._heartbeat_interval
        )
        
        async with self._lock:
            self._agents[agent.agent_id] = agent
            for cap in capabilities:
                self._capability_index[cap].append(agent.agent_id)
        
        logger.info(f"Agent {name} ({agent.agent_id}) registered with capabilities: {capabilities}")
        return agent
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销代理"""
        async with self._lock:
            if agent_id not in self._agents:
                return False
            
            agent = self._agents[agent_id]
            
            # 从能力索引中移除
            for cap in agent.capabilities:
                if agent_id in self._capability_index[cap]:
                    self._capability_index[cap].remove(agent_id)
            
            del self._agents[agent_id]
        
        logger.info(f"Agent {agent_id} unregistered")
        return True
    
    async def heartbeat(
        self,
        agent_id: str,
        metrics_update: Optional[Dict[str, Any]] = None
    ) -> bool:
        """处理代理心跳"""
        async with self._lock:
            if agent_id not in self._agents:
                logger.warning(f"Heartbeat from unknown agent: {agent_id}")
                return False
            
            agent = self._agents[agent_id]
            now = datetime.now()
            
            # 计算心跳延迟
            if agent.metrics.last_heartbeat:
                latency = (now - agent.metrics.last_heartbeat).total_seconds() * 1000
                agent.metrics.heartbeat_latency_ms = latency
            
            agent.metrics.last_heartbeat = now
            agent.last_seen = now
            
            # 更新指标
            if metrics_update:
                for key, value in metrics_update.items():
                    if hasattr(agent.metrics, key):
                        setattr(agent.metrics, key, value)
            
            # 状态恢复
            if agent.status in (AgentStatus.UNRESPONSIVE, AgentStatus.DEGRADED):
                old_status = agent.status
                agent.status = AgentStatus.AVAILABLE if agent.current_tasks == 0 else AgentStatus.BUSY
                await self._emit_status_change(agent_id, old_status, agent.status)
            
            # 更新健康状态
            agent.metrics.update_success_rate()
        
        # 触发心跳回调
        for callback in self._heartbeat_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent_id, agent.metrics)
                else:
                    callback(agent_id, agent.metrics)
            except Exception as e:
                logger.error(f"Heartbeat callback error: {e}")
        
        return True
    
    async def assign_task(
        self,
        task_id: str,
        required_capabilities: Set[AgentCapability],
        priority: int = 1,
        timeout_seconds: float = 300.0,
        preferred_agent: Optional[str] = None
    ) -> Optional[TaskAssignment]:
        """
        分配任务给合适的代理
        策略：优先选择高成功率、低负载的代理
        """
        async with self._lock:
            agent_id = await self._select_best_agent(
                required_capabilities,
                preferred_agent
            )
            
            if not agent_id:
                logger.warning(f"No available agent for task {task_id}")
                return None
            
            agent = self._agents[agent_id]
            agent.current_tasks += 1
            agent.status = AgentStatus.BUSY
            
            assignment = TaskAssignment(
                task_id=task_id,
                agent_id=agent_id,
                assigned_at=datetime.now(),
                timeout_at=datetime.now() + timedelta(seconds=timeout_seconds),
                priority=priority
            )
            
            self._assignments[task_id] = assignment
            logger.info(f"Task {task_id} assigned to agent {agent_id}")
            return assignment
    
    async def _select_best_agent(
        self,
        capabilities: Set[AgentCapability],
        preferred: Optional[str] = None
    ) -> Optional[str]:
        """选择最佳代理"""
        candidates = []
        
        # 检查首选代理
        if preferred and preferred in self._agents:
            agent = self._agents[preferred]
            if agent.is_available() and capabilities.issubset(agent.capabilities):
                candidates.append(preferred)
        
        # 查找具有所需能力的代理
        if not candidates:
            for agent_id, agent in self._agents.items():
                if not agent.is_available():
                    continue
                if not capabilities.issubset(agent.capabilities):
                    continue
                candidates.append(agent_id)
        
        if not candidates:
            return None
        
        # 评分排序：成功率 * 0.4 + (1-负载率) * 0.3 + (1-延迟归一化) * 0.2 + 优先级权重 * 0.1
        def score_agent(agent_id: str) -> float:
            agent = self._agents[agent_id]
            load_ratio = agent.current_tasks / agent.max_tasks if agent.max_tasks > 0 else 1.0
            latency_score = max(0, 1 - agent.metrics.heartbeat_latency_ms / 1000)
            
            return (
                agent.metrics.success_rate * 0.4 +
                (1 - load_ratio) * 0.3 +
                latency_score * 0.2 +
                (1 / agent.priority) * 0.1
            )
        
        return max(candidates, key=score_agent)
    
    async def release_task(self, task_id: str, success: bool = True):
        """释放任务，更新代理状态"""
        async with self._lock:
            if task_id not in self._assignments:
                return
            
            assignment = self._assignments[task_id]
            agent_id = assignment.agent_id
            
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.current_tasks = max(0, agent.current_tasks - 1)
                
                if success:
                    agent.metrics.tasks_completed += 1
                else:
                    agent.metrics.tasks_failed += 1
                
                agent.metrics.update_success_rate()
                
                # 更新状态
                if agent.current_tasks == 0:
                    agent.status = AgentStatus.AVAILABLE if agent.is_healthy() else AgentStatus.DEGRADED
            
            del self._assignments[task_id]
    
    async def handle_failure(
        self,
        task_id: str,
        agent_id: str,
        error: str,
        retry_with_fallback: bool = True
    ) -> Optional[TaskAssignment]:
        """处理任务失败，尝试故障转移"""
        logger.warning(f"Task {task_id} failed on agent {agent_id}: {error}")
        
        async with self._lock:
            agent = self._agents.get(agent_id)
            if agent:
                agent.metrics.tasks_failed += 1
                agent.metrics.update_success_rate()
                
                # 如果成功率过低，标记为降级
                if agent.metrics.success_rate < 0.5:
                    old_status = agent.status
                    agent.status = AgentStatus.DEGRADED
                    await self._emit_status_change(agent_id, old_status, AgentStatus.DEGRADED)
        
        # 释放原任务
        await self.release_task(task_id, success=False)
        
        if retry_with_fallback and task_id in self._assignments:
            # 获取原任务信息
            assignment = self._assignments[task_id]
            
            # 查找故障转移目标
            if agent and agent.failover_targets:
                for fallback_id in agent.failover_targets:
                    if fallback_id in self._agents:
                        fallback = self._agents[fallback_id]
                        if fallback.is_available():
                            logger.info(f"Failing over task {task_id} to {fallback_id}")
                            
                            # 触发故障转移回调
                            for callback in self._failover_callbacks:
                                try:
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(agent_id, fallback_id)
                                    else:
                                        callback(agent_id, fallback_id)
                                except Exception as e:
                                    logger.error(f"Failover callback error: {e}")
                            
                            return await self.assign_task(
                                task_id=task_id,
                                required_capabilities=fallback.capabilities,
                                preferred_agent=fallback_id
                            )
        
        return None
    
    async def _monitor_loop(self):
        """监控循环 - 检查代理健康状态"""
        while not self._shutdown:
            try:
                await self._check_agent_health()
                await asyncio.sleep(self._health_check_interval)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(5)
    
    async def _check_agent_health(self):
        """检查代理健康状态"""
        now = datetime.now()
        
        async with self._lock:
            for agent_id, agent in self._agents.items():
                if agent.status == AgentStatus.OFFLINE:
                    continue
                
                # 检查心跳超时
                if agent.metrics.last_heartbeat:
                    time_since_heartbeat = (now - agent.metrics.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self._heartbeat_timeout:
                        old_status = agent.status
                        agent.status = AgentStatus.UNRESPONSIVE
                        logger.warning(f"Agent {agent_id} marked as UNRESPONSIVE (no heartbeat for {time_since_heartbeat:.0f}s)")
                        await self._emit_status_change(agent_id, old_status, AgentStatus.UNRESPONSIVE)
                    elif time_since_heartbeat > self._heartbeat_timeout * 0.5:
                        # 心跳延迟，标记为降级
                        if agent.status not in (AgentStatus.DEGRADED, AgentStatus.UNRESPONSIVE):
                            old_status = agent.status
                            agent.status = AgentStatus.DEGRADED
                            logger.warning(f"Agent {agent_id} marked as DEGRADED")
                            await self._emit_status_change(agent_id, old_status, AgentStatus.DEGRADED)
    
    async def _emit_status_change(self, agent_id: str, old_status: AgentStatus, new_status: AgentStatus):
        """触发状态变化事件"""
        for callback in self._status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent_id, old_status, new_status)
                else:
                    callback(agent_id, old_status, new_status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def on_heartbeat(self, callback: Callable[[str, AgentMetrics], None]):
        """注册心跳回调"""
        self._heartbeat_callbacks.append(callback)
    
    def on_status_change(self, callback: Callable[[str, AgentStatus, AgentStatus], None]):
        """注册状态变化回调"""
        self._status_callbacks.append(callback)
    
    def on_failover(self, callback: Callable[[str, str], None]):
        """注册故障转移回调"""
        self._failover_callbacks.append(callback)
    
    async def get_agent(self, agent_id: str) -> Optional[SubAgent]:
        """获取代理信息"""
        async with self._lock:
            return self._agents.get(agent_id)
    
    async def get_agents_by_capability(self, capability: AgentCapability) -> List[SubAgent]:
        """按能力获取代理列表"""
        async with self._lock:
            agent_ids = self._capability_index.get(capability, [])
            return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def get_all_agents(self) -> List[SubAgent]:
        """获取所有代理"""
        return list(self._agents.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取协调器统计信息"""
        total_agents = len(self._agents)
        status_counts = defaultdict(int)
        total_tasks = 0
        
        for agent in self._agents.values():
            status_counts[agent.status.name] += 1
            total_tasks += agent.current_tasks
        
        return {
            'total_agents': total_agents,
            'active_tasks': len(self._assignments),
            'total_running_tasks': total_tasks,
            'status_distribution': dict(status_counts),
            'capability_distribution': {
                cap.name: len(aids) for cap, aids in self._capability_index.items()
            }
        }


# 全局协调器实例
_default_coordinator: Optional[AgentCoordinator] = None


def get_coordinator() -> AgentCoordinator:
    """获取全局代理协调器实例"""
    global _default_coordinator
    if _default_coordinator is None:
        _default_coordinator = AgentCoordinator()
    return _default_coordinator
