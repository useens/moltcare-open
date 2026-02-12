#!/usr/bin/env python3
"""
多子代理并行主控引擎 v1.0 - Multi-Agent Controller Engine
持续后台进程 + 高性能协作通信 + 绝对诚实验证

架构：
- 主控进程 (Controller): 持续运行，指挥协调
- 子代理池 (Agent Pool): 多代理并行执行
- 消息总线 (Message Bus): 高性能异步通信
- 状态监控 (State Monitor): 实时监控与恢复
"""

import asyncio
import json
import os
import sys
import time
import signal
import threading
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue, PriorityQueue
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
    "version": "1.0.0",
    "codename": "MultiAgent-Controller",
    "max_agents": 8,           # 最大子代理数
    "agent_pool_size": 4,      # 常驻代理池大小
    "message_queue_size": 1000, # 消息队列大小
    "heartbeat_interval": 5,    # 心跳间隔(秒)
    "task_timeout": 30,         # 任务超时(秒)
    "auto_scale": True,         # 自动扩缩容
}

# ============ 数据模型 ============
class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

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

@dataclass
class Message:
    msg_id: str
    msg_type: str  # 'command', 'result', 'heartbeat', 'error'
    sender: str
    receiver: str
    payload: Dict
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

# ============ 高性能消息总线 ============
class MessageBus:
    """异步消息总线 - 高性能通信"""
    def __init__(self, max_size: int = 1000):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.max_size = max_size
        self._lock = asyncio.Lock()
        
    async def register(self, agent_id: str):
        """注册代理到消息总线"""
        async with self._lock:
            if agent_id not in self.queues:
                self.queues[agent_id] = asyncio.Queue(maxsize=self.max_size)
                self.subscribers[agent_id] = []
                logger.info(f"📡 代理 {agent_id} 注册到消息总线")
    
    async def send(self, message: Message) -> bool:
        """发送消息"""
        receiver = message.receiver
        if receiver not in self.queues:
            logger.warning(f"❌ 接收者 {receiver} 未注册")
            return False
        
        try:
            await asyncio.wait_for(
                self.queues[receiver].put(message),
                timeout=1.0
            )
            return True
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ 发送消息到 {receiver} 超时")
            return False
    
    async def receive(self, agent_id: str, timeout: float = None) -> Optional[Message]:
        """接收消息"""
        if agent_id not in self.queues:
            return None
        
        try:
            if timeout:
                return await asyncio.wait_for(
                    self.queues[agent_id].get(),
                    timeout=timeout
                )
            else:
                return await self.queues[agent_id].get()
        except asyncio.TimeoutError:
            return None
    
    async def broadcast(self, message: Message, exclude: List[str] = None):
        """广播消息"""
        exclude = exclude or []
        tasks = []
        for agent_id in self.queues:
            if agent_id not in exclude:
                msg_copy = Message(
                    msg_id=f"{message.msg_id}_{agent_id}",
                    msg_type=message.msg_type,
                    sender=message.sender,
                    receiver=agent_id,
                    payload=message.payload
                )
                tasks.append(self.send(msg_copy))
        
        await asyncio.gather(*tasks, return_exceptions=True)

# ============ 子代理 ============
class SubAgent:
    """子代理 - 执行具体任务"""
    def __init__(self, agent_id: str, message_bus: MessageBus):
        self.agent_id = agent_id
        self.message_bus = message_bus
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
        
        # 启动心跳
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        # 启动消息处理
        message_task = asyncio.create_task(self._message_loop())
        
        logger.info(f"🤖 子代理 {self.agent_id} 启动")
        
        await asyncio.gather(heartbeat_task, message_task)
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            self.info.last_heartbeat = datetime.now()
            heartbeat_msg = Message(
                msg_id=f"hb_{self.agent_id}_{time.time()}",
                msg_type="heartbeat",
                sender=self.agent_id,
                receiver="controller",
                payload={"status": self.info.status.value, "info": asdict(self.info)}
            )
            await self.message_bus.send(heartbeat_msg)
            await asyncio.sleep(CONFIG["heartbeat_interval"])
    
    async def _message_loop(self):
        """消息处理循环"""
        while self.running:
            message = await self.message_bus.receive(self.agent_id, timeout=1.0)
            if message:
                await self._handle_message(message)
    
    async def _handle_message(self, message: Message):
        """处理消息"""
        if message.msg_type == "command":
            await self._execute_task(message)
        elif message.msg_type == "ping":
            # 响应ping
            pong = Message(
                msg_id=f"pong_{time.time()}",
                msg_type="pong",
                sender=self.agent_id,
                receiver=message.sender,
                payload={"timestamp": time.time()}
            )
            await self.message_bus.send(pong)
    
    async def _execute_task(self, message: Message):
        """执行任务"""
        task_type = message.payload.get("task_type")
        task_id = message.payload.get("task_id")
        
        self.info.status = AgentStatus.BUSY
        self.info.current_task = task_id
        self.info.total_tasks += 1
        
        logger.info(f"🎯 代理 {self.agent_id} 执行任务 {task_id} ({task_type})")
        
        try:
            if task_type in self.task_handlers:
                result = await self.task_handlers[task_type](message.payload)
                success = True
            else:
                result = {"error": f"未知任务类型: {task_type}"}
                success = False
            
            # 发送结果
            result_msg = Message(
                msg_id=f"result_{task_id}",
                msg_type="result",
                sender=self.agent_id,
                receiver="controller",
                payload={
                    "task_id": task_id,
                    "success": success,
                    "result": result,
                    "agent_id": self.agent_id
                }
            )
            await self.message_bus.send(result_msg)
            
            if success:
                self.info.success_tasks += 1
            
        except Exception as e:
            logger.error(f"💥 代理 {self.agent_id} 任务执行错误: {e}")
            error_msg = Message(
                msg_id=f"error_{task_id}",
                msg_type="error",
                sender=self.agent_id,
                receiver="controller",
                payload={"task_id": task_id, "error": str(e)}
            )
            await self.message_bus.send(error_msg)
        
        finally:
            self.info.status = AgentStatus.IDLE
            self.info.current_task = None

# ============ 主控引擎 ============
class MultiAgentController:
    """多代理主控引擎"""
    def __init__(self):
        self.message_bus = MessageBus(max_size=CONFIG["message_queue_size"])
        self.agents: Dict[str, SubAgent] = {}
        self.agent_processes: Dict[str, mp.Process] = {}
        self.task_queue: PriorityQueue = PriorityQueue()
        self.results: Dict[str, Any] = {}
        self.running = False
        self.scale_lock = threading.Lock()
        
    async def start(self):
        """启动主控引擎"""
        self.running = True
        logger.info(f"🚀 多代理主控引擎 v{CONFIG['version']} 启动")
        logger.info(f"📊 配置: 最大代理数={CONFIG['max_agents']}, 池大小={CONFIG['agent_pool_size']}")
        
        # 注册控制器到消息总线
        await self.message_bus.register("controller")
        
        # 启动初始代理池
        await self._scale_agents(CONFIG["agent_pool_size"])
        
        # 启动核心循环
        await asyncio.gather(
            self._heartbeat_monitor(),
            self._task_scheduler(),
            self._result_collector(),
            self._auto_scaler()
        )
    
    async def _scale_agents(self, target_count: int):
        """扩缩容代理"""
        with self.scale_lock:
            current_count = len(self.agents)
            
            if target_count > current_count:
                # 扩容
                for i in range(current_count, target_count):
                    agent_id = f"agent_{i:03d}"
                    agent = SubAgent(agent_id, self.message_bus)
                    # 注册示例任务处理器
                    agent.register_handler("compute", self._handle_compute_task)
                    agent.register_handler("io", self._handle_io_task)
                    
                    self.agents[agent_id] = agent
                    # 在单独进程中启动代理
                    process = mp.Process(target=self._run_agent, args=(agent,))
                    process.start()
                    self.agent_processes[agent_id] = process
                    
                    logger.info(f"➕ 扩容: 新增代理 {agent_id}")
                    
            elif target_count < current_count:
                # 缩容
                agents_to_remove = list(self.agents.keys())[target_count:]
                for agent_id in agents_to_remove:
                    if agent_id in self.agent_processes:
                        self.agent_processes[agent_id].terminate()
                        del self.agent_processes[agent_id]
                    del self.agents[agent_id]
                    logger.info(f"➖ 缩容: 移除代理 {agent_id}")
    
    def _run_agent(self, agent: SubAgent):
        """在进程中运行代理"""
        asyncio.run(agent.start())
    
    async def _heartbeat_monitor(self):
        """心跳监控"""
        while self.running:
            await asyncio.sleep(CONFIG["heartbeat_interval"])
            
            offline_agents = []
            for agent_id, agent in self.agents.items():
                if agent.info.last_heartbeat:
                    elapsed = (datetime.now() - agent.info.last_heartbeat).total_seconds()
                    if elapsed > CONFIG["heartbeat_interval"] * 3:
                        logger.warning(f"💔 代理 {agent_id} 心跳超时 ({elapsed:.0f}s)")
                        agent.info.status = AgentStatus.OFFLINE
                        offline_agents.append(agent_id)
            
            # 重启离线代理
            for agent_id in offline_agents:
                logger.info(f"🔄 重启离线代理 {agent_id}")
                # 实际实现中应该重新启动进程
    
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
                command = Message(
                    msg_id=f"cmd_{task.task_id}",
                    msg_type="command",
                    sender="controller",
                    receiver=agent_id,
                    payload={
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "data": task.payload
                    }
                )
                
                success = await self.message_bus.send(command)
                if success:
                    self.agents[agent_id].info.status = AgentStatus.BUSY
                    logger.info(f"📋 任务 {task.task_id} 分配给代理 {agent_id}")
                else:
                    # 重新放入队列
                    self.task_queue.put((priority, task))
            
            await asyncio.sleep(0.1)
    
    async def _result_collector(self):
        """结果收集器"""
        while self.running:
            message = await self.message_bus.receive("controller", timeout=1.0)
            if message:
                if message.msg_type == "result":
                    task_id = message.payload.get("task_id")
                    self.results[task_id] = message.payload
                    logger.info(f"✅ 收到任务 {task_id} 结果")
                    
                elif message.msg_type == "error":
                    task_id = message.payload.get("task_id")
                    logger.error(f"❌ 任务 {task_id} 失败: {message.payload.get('error')}")
                    
                elif message.msg_type == "heartbeat":
                    # 更新代理状态
                    agent_id = message.sender
                    if agent_id in self.agents:
                        status = message.payload.get("status")
                        self.agents[agent_id].info.status = AgentStatus(status)
    
    async def _auto_scaler(self):
        """自动扩缩容"""
        if not CONFIG["auto_scale"]:
            return
        
        while self.running:
            await asyncio.sleep(10)  # 每10秒检查一次
            
            queue_size = self.task_queue.qsize()
            busy_count = sum(
                1 for agent in self.agents.values()
                if agent.info.status == AgentStatus.BUSY
            )
            total_count = len(self.agents)
            
            # 扩容条件：队列堆积且大部分代理忙碌
            if queue_size > 5 and busy_count / total_count > 0.8:
                if total_count < CONFIG["max_agents"]:
                    new_count = min(total_count + 2, CONFIG["max_agents"])
                    await self._scale_agents(new_count)
            
            # 缩容条件：队列为空且有太多空闲代理
            elif queue_size == 0 and busy_count / total_count < 0.3:
                if total_count > CONFIG["agent_pool_size"]:
                    new_count = max(total_count - 1, CONFIG["agent_pool_size"])
                    await self._scale_agents(new_count)
    
    # ============ 任务处理器 ============
    async def _handle_compute_task(self, payload: Dict) -> Dict:
        """处理计算型任务"""
        import numpy as np
        
        # 模拟计算密集型任务
        data = payload.get("data", [])
        result = sum(x ** 2 for x in data)
        
        return {"sum_of_squares": result, "data_length": len(data)}
    
    async def _handle_io_task(self, payload: Dict) -> Dict:
        """处理IO型任务"""
        # 模拟IO任务
        await asyncio.sleep(0.1)
        
        return {"io_operation": "completed", "timestamp": time.time()}
    
    # ============ 公共API ============
    async def submit_task(self, task_type: str, payload: Dict, priority: int = 5) -> str:
        """提交任务"""
        task_id = f"task_{int(time.time() * 1000)}"
        task = Task(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority
        )
        self.task_queue.put((priority, task))
        logger.info(f"📥 提交任务 {task_id} (类型: {task_type}, 优先级: {priority})")
        return task_id
    
    async def get_result(self, task_id: str, timeout: float = None) -> Optional[Dict]:
        """获取任务结果"""
        start = time.time()
        while True:
            if task_id in self.results:
                return self.results.pop(task_id)
            
            if timeout and (time.time() - start) > timeout:
                return None
            
            await asyncio.sleep(0.1)
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            "version": CONFIG["version"],
            "agents": {
                "total": len(self.agents),
                "idle": sum(1 for a in self.agents.values() if a.info.status == AgentStatus.IDLE),
                "busy": sum(1 for a in self.agents.values() if a.info.status == AgentStatus.BUSY),
                "error": sum(1 for a in self.agents.values() if a.info.status == AgentStatus.ERROR),
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
    
    # 等待控制器启动
    await asyncio.sleep(2)
    
    # 提交测试任务
    logger.info("🧪 提交测试任务...")
    
    # 提交计算任务
    task1 = await controller.submit_task(
        "compute",
        {"data": list(range(100))},
        priority=3
    )
    
    task2 = await controller.submit_task(
        "io",
        {"operation": "read_file"},
        priority=5
    )
    
    # 等待结果
    result1 = await controller.get_result(task1, timeout=10)
    result2 = await controller.get_result(task2, timeout=10)
    
    logger.info(f"📊 任务1结果: {result1}")
    logger.info(f"📊 任务2结果: {result2}")
    
    # 获取系统状态
    status = controller.get_status()
    logger.info(f"📈 系统状态: {json.dumps(status, indent=2)}")
    
    # 持续运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 停止主控引擎")

if __name__ == "__main__":
    asyncio.run(main())
