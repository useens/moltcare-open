#!/usr/bin/env python3
"""
多代理控制器 v3.0 - Multi-Agent Controller
架构: 主控进程 + 线程池 + 安全队列
验证: 内置自检验证机制
"""

import asyncio
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MultiAgentController')

# ============ 配置 ============
CONFIG = {
    "version": "3.0.0",
    "max_workers": 4,
    "heartbeat_interval": 2,
    "task_timeout": 10,
}

# ============ 数据模型 ============
class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"

@dataclass
class Task:
    task_id: str
    task_type: str
    payload: Dict
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class TaskResult:
    task_id: str
    agent_id: str
    status: str
    result: Any
    completed_at: datetime = None
    
    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.now()

# ============ 子代理 ============
class SubAgent:
    """子代理 - 执行具体任务"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.status = AgentStatus.IDLE
        self.total_tasks = 0
        self.success_tasks = 0
        self.current_task = None
        self._lock = threading.Lock()
        
    def execute(self, task: Task) -> TaskResult:
        """执行任务"""
        with self._lock:
            self.status = AgentStatus.BUSY
            self.current_task = task.task_id
            self.total_tasks += 1
        
        logger.info(f"🤖 {self.agent_id} 执行 {task.task_id}")
        
        try:
            # 根据任务类型执行不同逻辑
            if task.task_type == "compute":
                result = self._compute_task(task.payload)
            elif task.task_type == "io":
                result = self._io_task(task.payload)
            elif task.task_type == "echo":
                result = task.payload
            else:
                result = {"error": f"未知任务类型: {task.task_type}"}
            
            with self._lock:
                self.success_tasks += 1
                self.status = AgentStatus.IDLE
                self.current_task = None
            
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="success",
                result=result
            )
            
        except Exception as e:
            logger.error(f"💥 {self.agent_id} 任务失败: {e}")
            with self._lock:
                self.status = AgentStatus.ERROR
                self.current_task = None
            
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="error",
                result=str(e)
            )
    
    def _compute_task(self, payload: Dict) -> Dict:
        """计算任务"""
        data = payload.get("data", [])
        # 模拟计算
        result = sum(x ** 2 for x in data)
        return {"sum_of_squares": result, "count": len(data)}
    
    def _io_task(self, payload: Dict) -> Dict:
        """IO任务"""
        time.sleep(0.1)
        return {"io_operation": "completed", "data": payload}
    
    def get_status(self) -> Dict:
        """获取状态"""
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "status": self.status.value,
                "current_task": self.current_task,
                "total_tasks": self.total_tasks,
                "success_tasks": self.success_tasks,
            }

# ============ 主控器 ============
class MultiAgentController:
    """多代理主控器"""
    
    def __init__(self):
        self.agents: Dict[str, SubAgent] = {}
        self.executor = ThreadPoolExecutor(max_workers=CONFIG["max_workers"])
        self.task_queue: Queue = Queue()
        self.results: Dict[str, TaskResult] = {}
        self.running = False
        self._lock = threading.Lock()
        
    def start(self):
        """启动控制器"""
        self.running = True
        logger.info(f"🚀 多代理控制器 v{CONFIG['version']} 启动")
        
        # 创建代理池
        for i in range(CONFIG["max_workers"]):
            agent_id = f"agent_{i:03d}"
            self.agents[agent_id] = SubAgent(agent_id)
            logger.info(f"   ✅ 代理 {agent_id} 就绪")
        
        # 启动后台任务
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        
    def submit_task(self, task_type: str, payload: Dict) -> str:
        """提交任务"""
        task_id = f"task_{int(time.time() * 1000)}_{id(payload) % 1000}"
        task = Task(task_id=task_id, task_type=task_type, payload=payload)
        
        with self._lock:
            self.task_queue.put(task)
        
        logger.info(f"📥 提交任务 {task_id} ({task_type})")
        return task_id
    
    def execute_sync(self, task_type: str, payload: Dict) -> TaskResult:
        """同步执行任务"""
        # 获取空闲代理
        agent = self._get_idle_agent()
        if not agent:
            logger.warning("❌ 无空闲代理")
            return TaskResult(
                task_id="failed",
                agent_id="none",
                status="failed",
                result="无空闲代理"
            )
        
        task = Task(
            task_id=f"sync_{int(time.time() * 1000)}",
            task_type=task_type,
            payload=payload
        )
        
        # 在线程池中执行
        future = self.executor.submit(agent.execute, task)
        try:
            result = future.result(timeout=CONFIG["task_timeout"])
            with self._lock:
                self.results[result.task_id] = result
            return result
        except Exception as e:
            logger.error(f"💥 任务执行异常: {e}")
            return TaskResult(
                task_id=task.task_id,
                agent_id=agent.agent_id,
                status="error",
                result=str(e)
            )
    
    def _get_idle_agent(self) -> Optional[SubAgent]:
        """获取空闲代理"""
        for agent in self.agents.values():
            if agent.status == AgentStatus.IDLE:
                return agent
        return None
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            time.sleep(CONFIG["heartbeat_interval"])
            # 可以在这里添加状态报告逻辑
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            "version": CONFIG["version"],
            "agents": {
                "total": len(self.agents),
                "idle": sum(1 for a in self.agents.values() if a.status == AgentStatus.IDLE),
                "busy": sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY),
                "error": sum(1 for a in self.agents.values() if a.status == AgentStatus.ERROR),
            },
            "results_stored": len(self.results),
        }
    
    def get_agent_status(self) -> List[Dict]:
        """获取所有代理状态"""
        return [agent.get_status() for agent in self.agents.values()]
    
    def stop(self):
        """停止控制器"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("🛑 控制器已停止")

# ============ 自检验证 ============
class SelfVerification:
    """自检验证机制"""
    
    @staticmethod
    def run_verification(controller: MultiAgentController) -> Dict:
        """运行自检验证"""
        logger.info("\n🔍 开始自检验证...")
        
        results = {
            "agent_creation": False,
            "task_execution": False,
            "concurrent_execution": False,
            "status_reporting": False,
            "overall": False,
        }
        
        # 1. 验证代理创建
        if len(controller.agents) == CONFIG["max_workers"]:
            results["agent_creation"] = True
            logger.info("   ✅ 代理创建: 通过")
        else:
            logger.error(f"   ❌ 代理创建: 失败 (期望{CONFIG['max_workers']}, 实际{len(controller.agents)})")
        
        # 2. 验证任务执行
        result = controller.execute_sync("echo", {"test": "data"})
        if result.status == "success":
            results["task_execution"] = True
            logger.info("   ✅ 任务执行: 通过")
        else:
            logger.error(f"   ❌ 任务执行: 失败 ({result.result})")
        
        # 3. 验证并发执行
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(controller.execute_sync, "compute", {"data": list(range(10))})
                for _ in range(4)
            ]
            concurrent_results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        if all(r.status == "success" for r in concurrent_results):
            results["concurrent_execution"] = True
            logger.info("   ✅ 并发执行: 通过")
        else:
            logger.error(f"   ❌ 并发执行: 失败")
        
        # 4. 验证状态报告
        status = controller.get_status()
        if status["agents"]["total"] > 0:
            results["status_reporting"] = True
            logger.info("   ✅ 状态报告: 通过")
        else:
            logger.error(f"   ❌ 状态报告: 失败")
        
        # 总体结果
        results["overall"] = all(results.values())
        
        logger.info(f"\n📊 验证结果: {'✅ 通过' if results['overall'] else '❌ 失败'}")
        return results

# ============ 主函数 ============
def main():
    """主函数 - 包含自检验证"""
    print(f"\n{'='*60}")
    print(f" 多代理控制器 v{CONFIG['version']} - 自检验证模式")
    print(f"{'='*60}\n")
    
    # 创建控制器
    controller = MultiAgentController()
    controller.start()
    
    # 等待启动
    time.sleep(1)
    
    # 运行自检验证
    verification = SelfVerification.run_verification(controller)
    
    # 显示状态
    print(f"\n{'='*60}")
    print(" 系统状态:")
    print(f"{'='*60}")
    status = controller.get_status()
    print(f"   版本: {status['version']}")
    print(f"   代理总数: {status['agents']['total']}")
    print(f"   空闲: {status['agents']['idle']}")
    print(f"   忙碌: {status['agents']['busy']}")
    print(f"   错误: {status['agents']['error']}")
    print(f"   结果存储: {status['results_stored']}")
    
    # 显示代理详情
    print(f"\n{'='*60}")
    print(" 代理详情:")
    print(f"{'='*60}")
    for agent_status in controller.get_agent_status():
        print(f"   {agent_status['agent_id']}: {agent_status['status']} "
              f"(任务: {agent_status['total_tasks']}, 成功: {agent_status['success_tasks']})")
    
    controller.stop()
    
    # 返回验证结果
    return verification["overall"]

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
