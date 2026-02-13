#!/usr/bin/env python3
"""
多代理控制器 v4.0 - 复杂任务调控版
升级: 外部API接口 + 主会话调用 + 复杂任务分解
"""

import asyncio
import json
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue, PriorityQueue
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MultiAgentController')

# ============ 配置 ============
CONFIG = {
    "version": "4.1.0",
    "max_workers": 50,        # 提升至50 (原20, 利用解除的系统限制)
    "task_timeout": 30,
    "api_enabled": True,
    "complex_task_decomposition": True,
    "unlimited_mode": True,   # 新增: 无限制模式
}

# ============ 数据模型 ============
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskPriority(Enum):
    P0 = 0  # 紧急
    P1 = 1  # 高
    P2 = 2  # 中
    P3 = 3  # 低

@dataclass
class SubTask:
    subtask_id: str
    parent_task_id: str
    task_type: str
    payload: Dict
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Any = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ComplexTask:
    task_id: str
    description: str
    subtasks: List[SubTask]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

# ============ 子代理 ============
class SubAgent:
    """子代理 - 执行具体任务"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.status = TaskStatus.PENDING
        self.current_task = None
        self.total_tasks = 0
        self.success_tasks = 0
        self._lock = threading.Lock()
        self.task_handlers: Dict[str, Callable] = {
            "compute": self._handle_compute,
            "io": self._handle_io,
            "analysis": self._handle_analysis,
            "extract": self._handle_extract,
            "summarize": self._handle_summarize,
        }
    
    def execute(self, subtask: SubTask) -> SubTask:
        """执行子任务"""
        with self._lock:
            self.status = TaskStatus.RUNNING
            self.current_task = subtask.subtask_id
            self.total_tasks += 1
            subtask.assigned_agent = self.agent_id
            subtask.started_at = datetime.now()
        
        logger.info(f"🤖 {self.agent_id} 执行 {subtask.subtask_id} ({subtask.task_type})")
        
        try:
            handler = self.task_handlers.get(subtask.task_type, self._handle_unknown)
            result = handler(subtask.payload)
            
            subtask.result = result
            subtask.status = TaskStatus.COMPLETED
            subtask.completed_at = datetime.now()
            
            with self._lock:
                self.success_tasks += 1
                self.status = TaskStatus.PENDING
                self.current_task = None
            
            logger.info(f"✅ {subtask.subtask_id} 完成")
            
        except Exception as e:
            logger.error(f"💥 {subtask.subtask_id} 失败: {e}")
            subtask.status = TaskStatus.FAILED
            subtask.result = str(e)
            subtask.completed_at = datetime.now()
            
            with self._lock:
                self.status = TaskStatus.PENDING
                self.current_task = None
        
        return subtask
    
    def _handle_compute(self, payload: Dict) -> Dict:
        """计算任务"""
        data = payload.get("data", [])
        operation = payload.get("operation", "sum")
        
        if operation == "sum":
            result = sum(data)
        elif operation == "mean":
            result = sum(data) / len(data) if data else 0
        elif operation == "max":
            result = max(data) if data else 0
        else:
            result = sum(x**2 for x in data)
        
        time.sleep(0.1)  # 模拟计算时间
        return {"operation": operation, "result": result, "input_size": len(data)}
    
    def _handle_io(self, payload: Dict) -> Dict:
        """IO任务"""
        operation = payload.get("operation", "read")
        target = payload.get("target", "default")
        
        time.sleep(0.2)  # 模拟IO时间
        return {"operation": operation, "target": target, "status": "completed"}
    
    def _handle_analysis(self, payload: Dict) -> Dict:
        """分析任务"""
        data = payload.get("data", [])
        analysis_type = payload.get("type", "basic")
        
        time.sleep(0.3)
        return {
            "type": analysis_type,
            "count": len(data),
            "summary": f"分析完成: {len(data)} 项数据",
        }
    
    def _handle_extract(self, payload: Dict) -> Dict:
        """提取任务"""
        source = payload.get("source", "default")
        count = payload.get("count", 5)
        
        time.sleep(0.2)
        return {
            "source": source,
            "extracted": count,
            "items": [f"item_{i}" for i in range(count)],
        }
    
    def _handle_summarize(self, payload: Dict) -> Dict:
        """总结任务"""
        content = payload.get("content", "")
        max_length = payload.get("max_length", 100)
        
        time.sleep(0.1)
        summary = content[:max_length] + "..." if len(content) > max_length else content
        return {"summary": summary, "original_length": len(content)}
    
    def _handle_unknown(self, payload: Dict) -> Dict:
        """未知任务类型"""
        return {"error": "未知任务类型", "payload": payload}
    
    def get_status(self) -> Dict:
        """获取代理状态"""
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "status": self.status.value,
                "current_task": self.current_task,
                "total_tasks": self.total_tasks,
                "success_tasks": self.success_tasks,
            }

# ============ 复杂任务分解器 ============
class TaskDecomposer:
    """复杂任务分解器"""
    
    @staticmethod
    def decompose(description: str, payload: Dict) -> ComplexTask:
        """将复杂任务分解为子任务"""
        task_id = f"complex_{int(time.time() * 1000)}"
        subtasks = []
        
        # 根据描述识别任务类型并分解
        if "网页采集" in description or "collect" in description.lower():
            subtasks = TaskDecomposer._decompose_web_collection(payload)
        elif "数据分析" in description or "analysis" in description.lower():
            subtasks = TaskDecomposer._decompose_data_analysis(payload)
        elif "情报处理" in description or "intel" in description.lower():
            subtasks = TaskDecomposer._decompose_intel_processing(payload)
        elif "批量处理" in description or "batch" in description.lower():
            subtasks = TaskDecomposer._decompose_batch_processing(payload)
        else:
            # 默认分解
            subtasks = [
                SubTask(
                    subtask_id=f"{task_id}_001",
                    parent_task_id=task_id,
                    task_type="compute",
                    payload=payload,
                    priority=TaskPriority.P1,
                )
            ]
        
        return ComplexTask(
            task_id=task_id,
            description=description,
            subtasks=subtasks,
        )
    
    @staticmethod
    def _decompose_web_collection(payload: Dict) -> List[SubTask]:
        """分解网页采集任务"""
        base_id = f"web_{int(time.time() * 1000)}"
        sources = payload.get("sources", ["hackernews", "github"])
        
        subtasks = []
        for i, source in enumerate(sources):
            subtasks.append(SubTask(
                subtask_id=f"{base_id}_extract_{i:03d}",
                parent_task_id=base_id,
                task_type="extract",
                payload={"source": source, "count": 10},
                priority=TaskPriority.P0 if i < 2 else TaskPriority.P1,
            ))
        
        # 添加分析子任务
        subtasks.append(SubTask(
            subtask_id=f"{base_id}_analyze",
            parent_task_id=base_id,
            task_type="analysis",
            payload={"type": "signal_scoring"},
            priority=TaskPriority.P1,
        ))
        
        # 添加总结子任务
        subtasks.append(SubTask(
            subtask_id=f"{base_id}_summarize",
            parent_task_id=base_id,
            task_type="summarize",
            payload={"max_length": 200},
            priority=TaskPriority.P2,
        ))
        
        return subtasks
    
    @staticmethod
    def _decompose_data_analysis(payload: Dict) -> List[SubTask]:
        """分解数据分析任务"""
        base_id = f"analysis_{int(time.time() * 1000)}"
        
        return [
            SubTask(
                subtask_id=f"{base_id}_compute",
                parent_task_id=base_id,
                task_type="compute",
                payload={"operation": "sum", "data": payload.get("data", [])},
                priority=TaskPriority.P0,
            ),
            SubTask(
                subtask_id=f"{base_id}_analysis",
                parent_task_id=base_id,
                task_type="analysis",
                payload={"type": "statistical"},
                priority=TaskPriority.P1,
            ),
        ]
    
    @staticmethod
    def _decompose_intel_processing(payload: Dict) -> List[SubTask]:
        """分解情报处理任务"""
        base_id = f"intel_{int(time.time() * 1000)}"
        
        return [
            SubTask(
                subtask_id=f"{base_id}_extract",
                parent_task_id=base_id,
                task_type="extract",
                payload={"source": "moltbook", "count": 5},
                priority=TaskPriority.P0,
            ),
            SubTask(
                subtask_id=f"{base_id}_extract2",
                parent_task_id=base_id,
                task_type="extract",
                payload={"source": "github", "count": 5},
                priority=TaskPriority.P0,
            ),
            SubTask(
                subtask_id=f"{base_id}_analyze",
                parent_task_id=base_id,
                task_type="analysis",
                payload={"type": "signal_ranking"},
                priority=TaskPriority.P1,
            ),
            SubTask(
                subtask_id=f"{base_id}_summarize",
                parent_task_id=base_id,
                task_type="summarize",
                payload={"max_length": 500},
                priority=TaskPriority.P2,
            ),
        ]
    
    @staticmethod
    def _decompose_batch_processing(payload: Dict) -> List[SubTask]:
        """分解批量处理任务"""
        base_id = f"batch_{int(time.time() * 1000)}"
        items = payload.get("items", [])
        
        subtasks = []
        for i, item in enumerate(items):
            subtasks.append(SubTask(
                subtask_id=f"{base_id}_process_{i:03d}",
                parent_task_id=base_id,
                task_type="compute",
                payload={"data": [item], "operation": payload.get("operation", "sum")},
                priority=TaskPriority.P1,
            ))
        
        return subtasks

# ============ 主控制器 ============
class MultiAgentController:
    """多代理控制器 - 支持复杂任务调控"""
    
    def __init__(self):
        self.agents: Dict[str, SubAgent] = {}
        self.executor = ThreadPoolExecutor(max_workers=CONFIG["max_workers"])
        self.task_queue = PriorityQueue()
        self.results: Dict[str, ComplexTask] = {}
        self.running = False
        self.decomposer = TaskDecomposer()
        self._lock = threading.Lock()
        
    def start(self):
        """启动控制器"""
        self.running = True
        logger.info(f"🚀 多代理控制器 v{CONFIG['version']} 启动")
        logger.info(f"   支持复杂任务分解 | API接口 | 20子代理")
        
        # 创建代理池
        for i in range(CONFIG["max_workers"]):
            agent_id = f"agent_{i:03d}"
            self.agents[agent_id] = SubAgent(agent_id)
            logger.info(f"   ✅ {agent_id} 就绪")
        
        # 启动调度器
        threading.Thread(target=self._scheduler_loop, daemon=True).start()
        
    def _scheduler_loop(self):
        """调度器循环"""
        while self.running:
            try:
                # 获取待处理子任务
                priority, subtask = self.task_queue.get(timeout=1)
                
                # 获取空闲代理
                agent = self._get_idle_agent()
                if agent:
                    self.executor.submit(self._execute_subtask, agent, subtask)
                else:
                    # 重新放入队列
                    self.task_queue.put((priority, subtask))
                    
            except:
                pass
    
    def _get_idle_agent(self) -> Optional[SubAgent]:
        """获取空闲代理"""
        for agent in self.agents.values():
            if agent.status == TaskStatus.PENDING:
                return agent
        return None
    
    def _execute_subtask(self, agent: SubAgent, subtask: SubTask):
        """执行子任务"""
        result = agent.execute(subtask)
        
        # 更新父任务状态
        with self._lock:
            parent_task = self.results.get(subtask.parent_task_id)
            if parent_task:
                all_completed = all(
                    st.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
                    for st in parent_task.subtasks
                )
                if all_completed:
                    parent_task.status = TaskStatus.COMPLETED
                    parent_task.completed_at = datetime.now()
    
    def submit_complex_task(self, description: str, payload: Dict) -> str:
        """提交复杂任务 - 外部API入口"""
        logger.info(f"📥 提交复杂任务: {description}")
        
        # 分解任务
        complex_task = self.decomposer.decompose(description, payload)
        
        with self._lock:
            self.results[complex_task.task_id] = complex_task
        
        # 将子任务加入队列
        for subtask in complex_task.subtasks:
            priority = (subtask.priority.value, subtask.created_at.timestamp())
            self.task_queue.put((priority, subtask))
        
        logger.info(f"   分解为 {len(complex_task.subtasks)} 个子任务")
        return complex_task.task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态 - 外部API入口"""
        task = self.results.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "description": task.description,
            "status": task.status.value,
            "subtasks_total": len(task.subtasks),
            "subtasks_completed": sum(1 for st in task.subtasks if st.status == TaskStatus.COMPLETED),
            "subtasks_failed": sum(1 for st in task.subtasks if st.status == TaskStatus.FAILED),
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }
    
    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """获取任务结果 - 外部API入口"""
        task = self.results.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "description": task.description,
            "status": task.status.value,
            "subtasks": [
                {
                    "subtask_id": st.subtask_id,
                    "task_type": st.task_type,
                    "status": st.status.value,
                    "assigned_agent": st.assigned_agent,
                    "result": st.result,
                }
                for st in task.subtasks
            ],
        }
    
    def get_system_status(self) -> Dict:
        """获取系统状态 - 外部API入口"""
        return {
            "version": CONFIG["version"],
            "agents": {
                "total": len(self.agents),
                "idle": sum(1 for a in self.agents.values() if a.status == TaskStatus.PENDING),
                "busy": sum(1 for a in self.agents.values() if a.status == TaskStatus.RUNNING),
            },
            "tasks": {
                "total": len(self.results),
                "completed": sum(1 for t in self.results.values() if t.status == TaskStatus.COMPLETED),
                "running": sum(1 for t in self.results.values() if t.status == TaskStatus.RUNNING),
                "pending": sum(1 for t in self.results.values() if t.status == TaskStatus.PENDING),
            },
        }
    
    def stop(self):
        """停止控制器"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("🛑 控制器已停止")

# ============ 命令行接口 ============
def main():
    """命令行接口 - 主会话可调用"""
    controller = MultiAgentController()
    controller.start()
    
    # 等待启动
    time.sleep(2)
    
    # 演示：提交复杂任务
    logger.info("\n" + "="*60)
    logger.info(" 演示: 复杂任务调控")
    logger.info("="*60)
    
    # 任务1: 网页采集
    task1_id = controller.submit_complex_task(
        "网页采集: Moltbook + GitHub Trending",
        {"sources": ["moltbook", "github", "hackernews"]}
    )
    
    # 任务2: 数据分析
    task2_id = controller.submit_complex_task(
        "数据分析: 批量统计",
        {"data": list(range(100)), "operation": "sum"}
    )
    
    # 等待任务完成
    logger.info("\n⏳ 等待任务完成...")
    time.sleep(3)
    
    # 获取结果
    for task_id in [task1_id, task2_id]:
        status = controller.get_task_status(task_id)
        result = controller.get_task_result(task_id)
        
        if status:
            logger.info(f"\n📋 任务 {task_id[:20]}...")
            logger.info(f"   描述: {status['description']}")
            logger.info(f"   状态: {status['status']}")
            logger.info(f"   子任务: {status['subtasks_completed']}/{status['subtasks_total']}")
            
            if result:
                logger.info(f"   子任务详情:")
                for st in result['subtasks'][:3]:  # 只显示前3个
                    logger.info(f"      {st['subtask_id'][-10:]}: {st['task_type']} -> {st['status']}")
    
    # 系统状态
    sys_status = controller.get_system_status()
    logger.info(f"\n📊 系统状态:")
    logger.info(f"   代理: {sys_status['agents']['idle']}/{sys_status['agents']['total']} 空闲")
    logger.info(f"   任务: {sys_status['tasks']['completed']}/{sys_status['tasks']['total']} 完成")
    
    controller.stop()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
