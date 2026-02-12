#!/usr/bin/env python3
"""
多子代理并行主控引擎 v1.1 - Multi-Agent Controller Engine
修复版：使用线程池实现可靠的多代理并行

架构：
- 主控进程 (Controller): 持续运行，指挥协调
- 线程池 (ThreadPool): 多代理并行执行（修正：使用线程而非进程）
- 消息总线 (MessageBus): 基于asyncio的高性能通信
- 任务调度 (TaskScheduler): 智能任务分配
"""

import asyncio
import json
import os
import sys
import time
import signal
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
from queue import PriorityQueue
import psutil
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/multi-agent-controller.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('MultiAgentController')

# ============ 配置 ============
CONFIG = {
    "version": "1.1.0",
    "codename": "MultiAgent-Fixed",
    "max_workers": 6,           # 最大工作线程
    "agent_count": 4,           # 子代理数量
    "task_timeout": 30,         # 任务超时(秒)
    "heartbeat_interval": 5,    # 心跳间隔(秒)
}

# ============ 数据模型 ============
class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"

@dataclass
class AgentInfo:
    agent_id: str
    status: AgentStatus
    current_task: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    total_tasks: int = 0
    success_tasks: int = 0
    
@dataclass
class Task:
    task_id: str
    task_type: str
    payload: Dict
    priority: int = 5
    created_at: datetime = None
    assigned_agent: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

# ============ 消息总线 ============
class MessageBus:
    """异步消息总线"""
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        
    async def register(self, agent_id: str):
        """注册代理"""
        if agent_id not in self.queues:
            self.queues[agent_id] = asyncio.Queue()
            logger.info(f"📡 注册: {agent_id}")
    
    async def send(self, target: str, message: Dict) -> bool:
        """发送消息"""
        if target not in self.queues:
            return False
        await self.queues[target].put(message)
        return True
    
    async def receive(self, agent_id: str, timeout: float = None) -> Optional[Dict]:
        """接收消息"""
        if agent_id not in self.queues:
            return None
        try:
            if timeout:
                return await asyncio.wait_for(self.queues[agent_id].get(), timeout)
            return await self.queues[agent_id].get()
        except asyncio.TimeoutError:
            return None

# ============ 子代理 ============
class SubAgent:
    """子代理"""
    def __init__(self, agent_id: str, message_bus: MessageBus, controller: 'MultiAgentController'):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.controller = controller
        self.info = AgentInfo(agent_id=agent_id, status=AgentStatus.IDLE)
        self.running = False
        self.task_handlers: Dict[str, Callable] = {}
        
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
        
    async def start(self):
        """启动代理"""
        self.running = True
        await self.message_bus.register(self.agent_id)
        logger.info(f"🤖 代理 {self.agent_id} 启动")
        
        # 启动核心循环
        await asyncio.gather(
            self._heartbeat_loop(),
            self._message_loop()
        )
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            self.info.last_heartbeat = datetime.now()
            await self.message_bus.send("controller", {
                "type": "heartbeat",
                "agent_id": self.agent_id,
                "status": self.info.status.value,
                "timestamp": time.time()
            })
            await asyncio.sleep(CONFIG["heartbeat_interval"])
    
    async def _message_loop(self):
        """消息处理循环"""
        while self.running:
            message = await self.message_bus.receive(self.agent_id, timeout=1.0)
            if message and message.get("type") == "task":
                await self._execute_task(message)
    
    async def _execute_task(self, message: Dict):
        """执行任务"""
        task_id = message.get("task_id")
        task_type = message.get("task_type")
        payload = message.get("payload", {})
        
        self.info.status = AgentStatus.BUSY
        self.info.current_task = task_id
        self.info.total_tasks += 1
        
        logger.info(f"🎯 {self.agent_id} 执行 {task_id}")
        
        try:
            if task_type in self.task_handlers:
                # 在线程池中执行阻塞任务
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.controller.executor,
                    self.task_handlers[task_type],
                    payload
                )
                success = True
            else:
                result = {"error": f"未知任务: {task_type}"}
                success = False
            
            # 发送结果
            await self.message_bus.send("controller", {
                "type": "result",
                "task_id": task_id,
                "agent_id": self.agent_id,
                "success": success,
                "result": result
            })
            
            if success:
                self.info.success_tasks += 1
                
        except Exception as e:
            logger.error(f"💥 {self.agent_id} 错误: {e}")
            await self.message_bus.send("controller", {
                "type": "error",
                "task_id": task_id,
                "agent_id": self.agent_id,
                "error": str(e)
            })
        
        finally:
            self.info.status = AgentStatus.IDLE
            self.info.current_task = None

# ============ 主控引擎 ============
class MultiAgentController:
    """多代理主控引擎"""
    def __init__(self):
        self.message_bus = MessageBus()
        self.agents: Dict[str, SubAgent] = {}
        self.executor = ThreadPoolExecutor(max_workers=CONFIG["max_workers"])
        self.task_queue: PriorityQueue = PriorityQueue()
        self.results: Dict[str, Any] = {}
        self.running = False
        self.stats_lock = threading.Lock()
        
    async def start(self):
        """启动主控引擎"""
        self.running = True
        logger.info(f"🚀 多代理主控引擎 v{CONFIG['version']} 启动")
        
        # 注册控制器
        await self.message_bus.register("controller")
        
        # 启动子代理
        for i in range(CONFIG["agent_count"]):
            agent_id = f"agent_{i:03d}"
            agent = SubAgent(agent_id, self.message_bus, self)
            agent.register_handler("compute", self._handle_compute)
            agent.register_handler("io", self._handle_io)
            self.agents[agent_id] = agent
            
            # 启动代理任务
            asyncio.create_task(agent.start())
        
        logger.info(f"📊 启动 {len(self.agents)} 个子代理")
        
        # 启动核心循环
        await asyncio.gather(
            self._task_scheduler(),
            self._result_collector()
        )
    
    def _handle_compute(self, payload: Dict) -> Dict:
        """计算任务处理器（在线程中运行）"""
        # 模拟计算
        import time
        time.sleep(0.1)
        
        data = payload.get("data", [])
        result = sum(x ** 2 for x in data)
        return {"sum_of_squares": result, "count": len(data)}
    
    def _handle_io(self, payload: Dict) -> Dict:
        """IO任务处理器（在线程中运行）"""
        import time
        time.sleep(0.05)
        
        return {"io_op": "completed", "timestamp": time.time()}
    
    async def _task_scheduler(self):
        """任务调度器"""
        while self.running:
            # 获取空闲代理
            idle_agents = [
                aid for aid, agent in self.agents.items()
                if agent.info.status == AgentStatus.IDLE
            ]
            
            if idle_agents and not self.task_queue.empty():
                priority, task = self.task_queue.get()
                agent_id = idle_agents[0]
                
                # 分配任务
                await self.message_bus.send(agent_id, {
                    "type": "task",
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "payload": task.payload
                })
                
                logger.info(f"📋 任务 {task.task_id} → {agent_id}")
            
            await asyncio.sleep(0.05)
    
    async def _result_collector(self):
        """结果收集器"""
        while self.running:
            message = await self.message_bus.receive("controller", timeout=1.0)
            if message:
                msg_type = message.get("type")
                
                if msg_type == "result":
                    task_id = message.get("task_id")
                    self.results[task_id] = message
                    logger.info(f"✅ 结果: {task_id}")
                    
                elif msg_type == "error":
                    task_id = message.get("task_id")
                    logger.error(f"❌ 失败: {task_id}")
                    
                elif msg_type == "heartbeat":
                    agent_id = message.get("agent_id")
                    if agent_id in self.agents:
                        status = message.get("status")
                        self.agents[agent_id].info.status = AgentStatus(status)
    
    async def submit_task(self, task_type: str, payload: Dict, priority: int = 5) -> str:
        """提交任务"""
        task_id = f"task_{int(time.time() * 1000)}_{id(payload) % 1000}"
        task = Task(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority
        )
        self.task_queue.put((priority, task))
        logger.info(f"📥 提交: {task_id} ({task_type})")
        return task_id
    
    async def get_result(self, task_id: str, timeout: float = None) -> Optional[Dict]:
        """获取结果"""
        start = time.time()
        while True:
            if task_id in self.results:
                return self.results.pop(task_id)
            
            if timeout and (time.time() - start) > timeout:
                return None
            
            await asyncio.sleep(0.05)
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "version": CONFIG["version"],
            "agents": {
                "total": len(self.agents),
                "idle": sum(1 for a in self.agents.values() if a.info.status == AgentStatus.IDLE),
                "busy": sum(1 for a in self.agents.values() if a.info.status == AgentStatus.BUSY),
            },
            "tasks": {
                "queued": self.task_queue.qsize(),
                "completed": len(self.results)
            }
        }

# ============ 主函数 ============
async def main():
    """主函数"""
    controller = MultiAgentController()
    
    # 启动控制器
    controller_task = asyncio.create_task(controller.start())
    
    # 等待启动
    await asyncio.sleep(2)
    
    # 提交测试任务
    logger.info("🧪 提交测试任务...")
    
    # 批量提交任务
    task_ids = []
    for i in range(10):
        task_id = await controller.submit_task(
            "compute",
            {"data": list(range(10 + i))},
            priority=5
        )
        task_ids.append(task_id)
    
    # 等待所有结果
    results = []
    for task_id in task_ids:
        result = await controller.get_result(task_id, timeout=30)
        if result:
            results.append(result)
    
    logger.info(f"📊 完成: {len(results)}/{len(task_ids)} 任务")
    
    # 获取系统状态
    status = controller.get_status()
    logger.info(f"📈 状态: {json.dumps(status, indent=2, default=str)}")
    
    # 持续运行
    try:
        while True:
            await asyncio.sleep(5)
            # 显示当前状态
            status = controller.get_status()
            logger.info(f"⏱️ 状态: {status['agents']['idle']}/{status['agents']['total']} 空闲, "
                       f"队列: {status['tasks']['queued']}, 完成: {status['tasks']['completed']}")
    except KeyboardInterrupt:
        logger.info("🛑 停止")

if __name__ == "__main__":
    asyncio.run(main())
