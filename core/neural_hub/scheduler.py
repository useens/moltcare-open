"""
神经中枢 2.0 - 智能调度引擎
任务分配和负载均衡
"""
import asyncio
import uuid
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 0   # 系统故障、安全事件
    HIGH = 1       # 用户紧急指令
    NORMAL = 2     # 高价值任务
    LOW = 3        # 常规任务
    BACKGROUND = 4 # 后台任务

class TaskStatus(Enum):
    """任务状态"""
    PENDING = 'pending'
    ASSIGNED = 'assigned'
    EXECUTING = 'executing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

@dataclass
class Task:
    """任务定义"""
    id: str
    type: str
    priority: TaskPriority
    payload: dict = field(default_factory=dict)
    required_capabilities: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    
    @property
    def is_urgent(self) -> bool:
        return self.priority in (TaskPriority.CRITICAL, TaskPriority.HIGH)

class SmartScheduler:
    """智能调度引擎"""
    
    def __init__(self, state_manager, database=None, redis_client=None):
        self.state_manager = state_manager
        self.database = database
        self.redis = redis_client
        
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running = False
        self._scheduler_task = None
        self._callbacks: List[Callable] = []
        
    def on_task_complete(self, callback: Callable):
        """注册任务完成回调"""
        self._callbacks.append(callback)
    
    def create_task(self, task_type: str, payload: dict = None,
                    priority: TaskPriority = TaskPriority.NORMAL,
                    required_capabilities: List[str] = None) -> Task:
        """创建任务"""
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        task = Task(
            id=task_id,
            type=task_type,
            priority=priority,
            payload=payload or {},
            required_capabilities=required_capabilities or [],
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        
        # 持久化
        if self.database:
            self.database.create_task(
                task_id, task_type, priority.value, payload
            )
        
        # 加入队列
        self.task_queue.put_nowait((priority.value, task.created_at.timestamp(), task_id))
        
        print(f"[Scheduler] 任务创建: {task_id} (优先级: {priority.name})")
        return task
    
    def submit_task(self, task_type: str, payload: dict = None,
                    priority: TaskPriority = TaskPriority.NORMAL,
                    required_capabilities: List[str] = None) -> str:
        """提交任务 (便捷方法)"""
        task = self.create_task(task_type, payload, priority, required_capabilities)
        return task.id
    
    async def process_queue(self):
        """处理任务队列"""
        while self._running:
            try:
                # 获取优先级最高的任务
                priority, timestamp, task_id = await asyncio.wait_for(
                    self.task_queue.get(), timeout=1.0
                )
                
                task = self.tasks.get(task_id)
                if not task or task.status != TaskStatus.PENDING:
                    continue
                
                # 分配任务
                assigned = await self._assign_task(task)
                
                if not assigned:
                    # 重新入队（稍后重试）
                    await asyncio.sleep(5)
                    self.task_queue.put_nowait((priority, timestamp, task_id))
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[Scheduler] 处理错误: {e}")
                await asyncio.sleep(1)
    
    async def _assign_task(self, task: Task) -> bool:
        """分配任务给合适的bot"""
        # 选择最佳bot
        bot = self.state_manager.get_best_bot_for_task(task.required_capabilities)
        
        if not bot:
            print(f"[Scheduler] 无可用bot: {task.id}")
            return False
        
        # 更新状态
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = bot.bot_id
        task.started_at = datetime.now()
        
        self.state_manager.update_state(bot.bot_id, 'busy', task.id)
        
        # 持久化
        if self.database:
            self.database.assign_task(task.id, bot.bot_id)
        
        # 发送指令
        if self.redis:
            await self.redis.assign_task(bot.bot_id, {
                'task_id': task.id,
                'type': task.type,
                'payload': task.payload
            })
        
        print(f"[Scheduler] 任务分配: {task.id} -> {bot.bot_id}")
        return True
    
    def complete_task(self, task_id: str, result: dict = None):
        """完成任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.result = result
        
        # 释放bot
        if task.assigned_to:
            self.state_manager.update_state(task.assigned_to, 'idle')
            self.state_manager.update_task_stats(task.assigned_to, True)
        
        # 持久化
        if self.database:
            self.database.complete_task(task_id, result)
        
        # 回调
        for callback in self._callbacks:
            try:
                callback(task)
            except Exception as e:
                print(f"[Scheduler] 回调错误: {e}")
        
        print(f"[Scheduler] 任务完成: {task_id}")
        return True
    
    def fail_task(self, task_id: str, error: str):
        """任务失败"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.error = error
        
        # 更新bot统计
        if task.assigned_to:
            self.state_manager.update_task_stats(task.assigned_to, False)
        
        # 重试逻辑
        if task.retry_count < 3:
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            task.assigned_to = None
            
            # 重新入队
            self.task_queue.put_nowait(
                (task.priority.value, task.created_at.timestamp(), task.id)
            )
            
            print(f"[Scheduler] 任务重试: {task_id} (第{task.retry_count}次)")
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            
            # 释放bot
            if task.assigned_to:
                self.state_manager.update_state(task.assigned_to, 'idle')
            
            print(f"[Scheduler] 任务失败: {task_id}")
        
        # 持久化
        if self.database:
            self.database.fail_task(task_id, error)
        
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task or task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            return False
        
        task.status = TaskStatus.CANCELLED
        
        # 释放bot
        if task.assigned_to:
            self.state_manager.update_state(task.assigned_to, 'idle')
        
        print(f"[Scheduler] 任务取消: {task_id}")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    def get_active_tasks(self) -> List[Task]:
        """获取活跃任务"""
        return [
            t for t in self.tasks.values()
            if t.status in (TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.EXECUTING)
        ]
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total = len(self.tasks)
        pending = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        executing = len([t for t in self.tasks.values() if t.status == TaskStatus.EXECUTING])
        completed = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        
        return {
            'total': total,
            'pending': pending,
            'executing': executing,
            'completed': completed,
            'failed': failed,
            'queue_size': self.task_queue.qsize()
        }
    
    async def start(self):
        """启动调度器"""
        self._running = True
        self._scheduler_task = asyncio.create_task(self.process_queue())
        print("[Scheduler] 调度器已启动")
    
    async def stop(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
        print("[Scheduler] 调度器已停止")
