"""
任务队列模块 - 优先级任务管理
支持优先级队列、超时处理、任务状态追踪
"""

import uuid
import heapq
import asyncio
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 0    # 关键任务，立即执行
    HIGH = 1        # 高优先级
    NORMAL = 2      # 普通优先级
    LOW = 3         # 低优先级
    BACKGROUND = 4  # 后台任务


class TaskStatus(Enum):
    """任务状态"""
    PENDING = auto()      # 等待执行
    RUNNING = auto()      # 执行中
    COMPLETED = auto()    # 已完成
    FAILED = auto()       # 失败
    CANCELLED = auto()    # 已取消
    TIMEOUT = auto()      # 超时
    RETRYING = auto()     # 重试中


@dataclass
class Task:
    """任务定义"""
    name: str
    payload: Any
    priority: TaskPriority = TaskPriority.NORMAL
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: float = 300.0  # 默认5分钟超时
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: float = 1.0  # 重试延迟秒数
    dependencies: Set[str] = field(default_factory=set)  # 依赖的任务ID
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    
    def __lt__(self, other):
        """用于堆排序：优先级数字小的先执行"""
        if not isinstance(other, Task):
            return NotImplemented
        return (self.priority.value, self.created_at) < (other.priority.value, other.created_at)


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0


class TaskQueue:
    """
    优先级任务队列
    支持异步执行、超时处理、依赖管理
    """
    
    def __init__(self, max_concurrent: int = 5):
        self._queue: List[Task] = []  # 优先队列
        self._tasks: Dict[str, Task] = {}  # 所有任务索引
        self._running: Dict[str, Task] = {}  # 执行中的任务
        self._completed: Dict[str, Task] = {}  # 已完成的任务
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._handlers: Dict[str, Callable] = {}
        self._event_callbacks: Dict[TaskStatus, List[Callable]] = {
            status: [] for status in TaskStatus
        }
        self._shutdown = False
        self._worker_task: Optional[asyncio.Task] = None
        self._max_concurrent = max_concurrent
        
    async def start(self):
        """启动任务队列处理器"""
        if self._worker_task is None or self._worker_task.done():
            self._shutdown = False
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("TaskQueue started")
    
    async def stop(self, wait_for_pending: bool = True):
        """停止任务队列"""
        self._shutdown = True
        if self._worker_task and not self._worker_task.done():
            if wait_for_pending and self._queue:
                logger.info(f"Waiting for {len(self._queue)} pending tasks...")
                await self.wait_until_empty(timeout=60)
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("TaskQueue stopped")
    
    async def submit(
        self,
        name: str,
        payload: Any,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 300.0,
        max_retries: int = 3,
        dependencies: Optional[Set[str]] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """提交新任务"""
        task = Task(
            name=name,
            payload=payload,
            priority=priority,
            timeout_seconds=timeout,
            max_retries=max_retries,
            dependencies=dependencies or set(),
            tags=tags or set(),
            metadata=metadata or {}
        )
        
        async with self._lock:
            self._tasks[task.task_id] = task
            heapq.heappush(self._queue, task)
            logger.debug(f"Task {task.task_id} ({name}) submitted with priority {priority.name}")
        
        await self._emit_event(TaskStatus.PENDING, task)
        return task
    
    async def submit_urgent(self, name: str, payload: Any, **kwargs) -> Task:
        """提交紧急任务（高优先级）"""
        return await self.submit(name, payload, priority=TaskPriority.CRITICAL, **kwargs)
    
    async def cancel(self, task_id: str) -> bool:
        """取消任务"""
        async with self._lock:
            if task_id in self._running:
                logger.warning(f"Cannot cancel running task {task_id}")
                return False
            
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = datetime.now()
                    # 从队列中移除
                    self._queue = [t for t in self._queue if t.task_id != task_id]
                    heapq.heapify(self._queue)
                    await self._emit_event(TaskStatus.CANCELLED, task)
                    logger.info(f"Task {task_id} cancelled")
                    return True
        return False
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        async with self._lock:
            return self._tasks.get(task_id)
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[Task]:
        """等待任务完成"""
        start = datetime.now()
        while True:
            task = await self.get_task(task_id)
            if task and task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT):
                return task
            
            if timeout and (datetime.now() - start).total_seconds() > timeout:
                return None
            
            await asyncio.sleep(0.1)
    
    async def wait_until_empty(self, timeout: Optional[float] = None):
        """等待直到队列为空"""
        start = datetime.now()
        while self._queue or self._running:
            if timeout and (datetime.now() - start).total_seconds() > timeout:
                break
            await asyncio.sleep(0.1)
    
    def register_handler(self, task_name: str, handler: Callable):
        """注册任务处理器"""
        self._handlers[task_name] = handler
        logger.debug(f"Handler registered for task type: {task_name}")
    
    def on_status_change(self, status: TaskStatus, callback: Callable):
        """注册状态变化回调"""
        self._event_callbacks[status].append(callback)
    
    async def _emit_event(self, status: TaskStatus, task: Task):
        """触发状态事件"""
        callbacks = self._event_callbacks.get(status, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task)
                else:
                    callback(task)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def _check_dependencies_ready(self, task: Task) -> bool:
        """检查任务依赖是否都已完成"""
        for dep_id in task.dependencies:
            if dep_id not in self._completed:
                return False
        return True
    
    async def _worker_loop(self):
        """工作循环"""
        while not self._shutdown:
            try:
                await self._process_next_task()
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)
    
    async def _process_next_task(self):
        """处理下一个任务"""
        async with self._lock:
            if not self._queue:
                await asyncio.sleep(0.1)
                return
            
            # 找到依赖已满足的最高优先级任务
            ready_task = None
            for i, task in enumerate(self._queue):
                if self._check_dependencies_ready(task):
                    ready_task = i
                    break
            
            if ready_task is None:
                await asyncio.sleep(0.1)
                return
            
            task = self._queue.pop(ready_task)
            heapq.heapify(self._queue)
        
        # 使用信号量限制并发
        async with self._semaphore:
            await self._execute_task(task)
    
    async def _execute_task(self, task: Task):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        async with self._lock:
            self._running[task.task_id] = task
        
        await self._emit_event(TaskStatus.RUNNING, task)
        logger.info(f"Executing task {task.task_id} ({task.name})")
        
        handler = self._handlers.get(task.name)
        if not handler:
            task.status = TaskStatus.FAILED
            task.error = f"No handler registered for task type: {task.name}"
            await self._complete_task(task)
            return
        
        try:
            # 设置超时
            result = await asyncio.wait_for(
                handler(task.payload) if asyncio.iscoroutinefunction(handler) 
                else asyncio.to_thread(handler, task.payload),
                timeout=task.timeout_seconds
            )
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            logger.info(f"Task {task.task_id} completed successfully")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.TIMEOUT
            task.error = f"Task timed out after {task.timeout_seconds}s"
            logger.warning(f"Task {task.task_id} timed out")
            
            # 重试逻辑
            if task.retry_count < task.max_retries:
                await self._retry_task(task)
                return
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task {task.task_id} failed: {e}")
            
            # 重试逻辑
            if task.retry_count < task.max_retries:
                await self._retry_task(task)
                return
        
        await self._complete_task(task)
    
    async def _retry_task(self, task: Task):
        """重试任务"""
        task.retry_count += 1
        task.status = TaskStatus.RETRYING
        logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries})")
        
        await self._emit_event(TaskStatus.RETRYING, task)
        
        # 指数退避
        delay = task.retry_delay * (2 ** (task.retry_count - 1))
        await asyncio.sleep(delay)
        
        async with self._lock:
            task.status = TaskStatus.PENDING
            heapq.heappush(self._queue, task)
    
    async def _complete_task(self, task: Task):
        """完成任务处理"""
        task.completed_at = datetime.now()
        
        async with self._lock:
            if task.task_id in self._running:
                del self._running[task.task_id]
            self._completed[task.task_id] = task
        
        await self._emit_event(task.status, task)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        return {
            'pending': len(self._queue),
            'running': len(self._running),
            'completed': len(self._completed),
            'max_concurrent': self._max_concurrent,
        }
    
    def get_pending_tasks(self) -> List[Task]:
        """获取所有待处理任务"""
        return sorted(self._queue, key=lambda t: (t.priority.value, t.created_at))
    
    def get_running_tasks(self) -> List[Task]:
        """获取执行中任务"""
        return list(self._running.values())


# 全局任务队列实例
_default_queue: Optional[TaskQueue] = None


def get_task_queue(max_concurrent: int = 5) -> TaskQueue:
    """获取全局任务队列实例"""
    global _default_queue
    if _default_queue is None:
        _default_queue = TaskQueue(max_concurrent=max_concurrent)
    return _default_queue
