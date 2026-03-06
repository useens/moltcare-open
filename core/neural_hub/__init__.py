"""
神经中枢 2.0 (Neural Hub V2)
完全重构的多Agent协作系统

核心组件:
- hub: 主服务
- state_manager: 状态管理
- scheduler: 智能调度
- database: SQLite持久化
- redis_client: Redis消息总线

使用示例:
    from core.neural_hub import NeuralHub
    
    hub = NeuralHub()
    await hub.start()
    
    # 提交任务
    task_id = await hub.submit_task(
        task_type='code_review',
        payload={'file': 'test.py'},
        priority=2,
        required_capabilities=['code_review']
    )
"""

from .hub import NeuralHub
from .state_manager import StateManager, BotState
from .scheduler import SmartScheduler, Task, TaskPriority, TaskStatus
from .database import TaskDatabase
from .redis_client import RedisClient

__version__ = '2.0.0'
__all__ = [
    'NeuralHub',
    'StateManager',
    'BotState',
    'SmartScheduler',
    'Task',
    'TaskPriority',
    'TaskStatus',
    'TaskDatabase',
    'RedisClient'
]
