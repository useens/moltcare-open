#!/usr/bin/env python3
"""
Command Center - Enhanced Bot Relay v2.0 (P0 Complete)
增强版Bot Relay - 整合任务队列、智能调度、自动恢复
"""

import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# 导入核心组件
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from task_queue import Task, TaskQueue, TaskPriority, get_queue
from scheduler import IntelligentScheduler, get_scheduler

# 节点配置
NANOBOTS = [
    {"id": "NB01", "port": 18801, "apikey": "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"},
    {"id": "NB02", "port": 18802, "apikey": "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"},
    {"id": "NB03", "port": 18803, "apikey": "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"},
    {"id": "NB04", "port": 18804, "apikey": "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"},
    {"id": "NB05", "port": 18805, "apikey": "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"},
    {"id": "NB06", "port": 18806, "apikey": "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"},
    {"id": "NB07", "port": 18807, "apikey": "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"},
    {"id": "NB08", "port": 18808, "apikey": "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"},
    {"id": "NB09", "port": 18809, "apikey": "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"},
    {"id": "NB10", "port": 18810, "apikey": "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"},
]

MODEL_MAP = {
    "step": "stepfun-ai/step-3.5-flash",
    "ds": "deepseek-ai/deepseek-v3.2"
}

class EnhancedBotRelay:
    """增强版Bot Relay"""
    
    def __init__(self):
        self.queue = get_queue()
        self.scheduler = get_scheduler()
    
    def check_node(self, node_id: str) -> bool:
        """检查节点状态"""
        node = next((n for n in NANOBOTS if n["id"] == node_id), None)
        if not node:
            return False
        try:
            resp = requests.get(f"http://127.0.0.1:{node['port']}/status", timeout=3)
            return resp.status_code == 200
        except:
            return False
    
    def execute_task(self, task: Task) -> tuple:
        """执行任务"""
        node = next((n for n in NANOBOTS if n["id"] == task.node_id), None)
        if not node:
            return False, "Node not found"
        
        # 确定模型
        node_num = int(task.node_id[2:])
        model_key = "step" if node_num <= 5 else "ds"
        model = MODEL_MAP[model_key]
        
        start_time = time.time()
        
        try:
            resp = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {node['apikey']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": task.prompt}],
                    "max_tokens": 500
                },
                timeout=45
            )
            
            duration = time.time() - start_time
            
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # 记录成功
                self.scheduler.record_result(task.node_id, task.task_type, True, duration)
                
                return True, content
            else:
                # 记录失败
                self.scheduler.record_result(task.node_id, task.task_type, False, 0)
                return False, f"HTTP {resp.status_code}"
                
        except Exception as e:
            self.scheduler.record_result(task.node_id, task.task_type, False, 0)
            return False, str(e)
    
    def process_queue(self, max_tasks: int = 10):
        """处理队列中的任务"""
        print(f"🔄 开始处理队列 (最多{max_tasks}个任务)...")
        
        processed = 0
        while processed < max_tasks:
            task = self.queue.dequeue()
            if not task:
                break
            
            print(f"📤 执行任务: {task.task_id} on {task.node_id}")
            
            success, result = self.execute_task(task)
            
            if success:
                self.queue.complete(task.task_id, result, task.node_id)
                print(f"✅ 任务完成: {task.task_id}")
            else:
                self.queue.fail(task.task_id, result, task.node_id)
                print(f"❌ 任务失败: {task.task_id} - {result}")
            
            processed += 1
            time.sleep(0.5)  # 避免 rate limit
        
        print(f"✅ 处理完成: {processed} 个任务")
        return processed
    
    def submit_task(self, prompt: str, priority: str = "normal", 
                   node_id: str = None, task_type: str = "auto") -> str:
        """提交任务"""
        # 转换优先级
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "normal": TaskPriority.NORMAL,
            "low": TaskPriority.LOW
        }
        task_priority = priority_map.get(priority, TaskPriority.NORMAL)
        
        # 提交任务
        task = self.scheduler.submit_task(prompt, task_priority, node_id, task_type)
        
        return task.task_id
    
    def get_queue_stats(self):
        """获取队列统计"""
        return self.queue.get_stats()
    
    def get_scheduler_stats(self):
        """获取调度器统计"""
        return self.scheduler.get_node_stats()

def main():
    import sys
    
    relay = EnhancedBotRelay()
    
    if len(sys.argv) < 2:
        print("Enhanced Bot Relay v2.0 (P0)")
        print("")
        print("Usage: nb_relay_v2.py <command> [options]")
        print("")
        print("Commands:")
        print("  submit <prompt> [--priority P] [--node NODE]  提交任务")
        print("  process [max_tasks]                            处理队列")
        print("  stats                                          查看统计")
        print("  queue                                          查看队列")
        print("")
        print("Priority: critical, high, normal, low")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "submit":
        if len(sys.argv) < 3:
            print("Usage: submit <prompt>")
            sys.exit(1)
        
        prompt = sys.argv[2]
        priority = "normal"
        node_id = None
        
        # 解析参数
        if "--priority" in sys.argv:
            idx = sys.argv.index("--priority")
            if idx + 1 < len(sys.argv):
                priority = sys.argv[idx + 1]
        
        if "--node" in sys.argv:
            idx = sys.argv.index("--node")
            if idx + 1 < len(sys.argv):
                node_id = sys.argv[idx + 1]
        
        task_id = relay.submit_task(prompt, priority, node_id)
        print(f"✅ 任务已提交: {task_id}")
    
    elif command == "process":
        max_tasks = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        relay.process_queue(max_tasks)
    
    elif command == "stats":
        print("=" * 60)
        print("📊 系统统计")
        print("=" * 60)
        
        # 队列统计
        queue_stats = relay.get_queue_stats()
        print("\n队列状态:")
        for status, count in queue_stats.items():
            print(f"  {status}: {count}")
        
        # 节点统计
        node_stats = relay.get_scheduler_stats()
        print("\n节点状态:")
        for node_id, stats in node_stats.items():
            print(f"  {node_id}: {stats['model']}, 成功率{stats['success_rate']}, 评分{stats['score']}")
        
        print("=" * 60)
    
    elif command == "queue":
        pending = relay.queue.get_pending_tasks()
        print(f"📋 待处理任务: {len(pending)}")
        for task in pending[:10]:
            print(f"  {task.task_id}: [{task.priority.value}] {task.prompt[:40]}... -> {task.node_id}")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
