"""
主-子代理协调系统
提供任务队列管理、代理协调、结果聚合功能
"""

from .task_queue import (
    TaskQueue, Task, TaskPriority, TaskStatus, 
    TaskResult, get_task_queue
)
from .agent_coordinator import (
    AgentCoordinator, SubAgent, AgentStatus, AgentCapability,
    AgentMetrics, TaskAssignment, get_coordinator
)
from .result_aggregator import (
    ResultAggregator, AggregationStrategy, AggregationContext,
    ResultItem, AggregationResult, ResultQuality, get_aggregator
)
from .orchestrator import (
    Orchestrator, SubTaskRequest, OrchestratedResult,
    create_orchestrator, submit_subtask
)

__all__ = [
    # Task Queue
    'TaskQueue',
    'Task',
    'TaskPriority',
    'TaskStatus',
    'TaskResult',
    'get_task_queue',
    # Agent Coordinator
    'AgentCoordinator',
    'SubAgent',
    'AgentStatus',
    'AgentCapability',
    'AgentMetrics',
    'TaskAssignment',
    'get_coordinator',
    # Result Aggregator
    'ResultAggregator',
    'AggregationStrategy',
    'AggregationContext',
    'ResultItem',
    'AggregationResult',
    'ResultQuality',
    'get_aggregator',
    # Orchestrator
    'Orchestrator',
    'SubTaskRequest',
    'OrchestratedResult',
    'create_orchestrator',
    'submit_subtask',
]

__version__ = '1.0.0'
