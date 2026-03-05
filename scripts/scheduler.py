#!/usr/bin/env python3
"""
Command Center - Task Scheduler
任务调度器

功能:
- 智能任务分配
- 负载均衡
- 失败重试
- 结果收集
"""

import json
import sys
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# 导入Bot Relay
sys.path.insert(0, str(Path(__file__).parent))
from nb_relay import NanobotRelay, NANOBOTS

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.relay = NanobotRelay()
        self.task_history = []
        self.node_stats = {node["id"]: {"success": 0, "fail": 0, "avg_time": 0} for node in NANOBOTS}
    
    def select_nodes(self, strategy="auto", count=1, task_type=None):
        """选择节点
        
        strategy:
        - auto: 根据任务类型自动选择
        - step: 选择Step组 (NB01-NB05)
        - ds: 选择DeepSeek组 (NB06-NB10)
        - random: 随机选择
        - round_robin: 轮询
        """
        if strategy == "auto":
            # 根据任务类型选择
            if task_type in ["quick", "simple", "fast"]:
                strategy = "step"
            elif task_type in ["deep", "complex", "reasoning"]:
                strategy = "ds"
            else:
                strategy = "round_robin"
        
        if strategy == "step":
            # Step组: NB01-NB05
            candidates = [n for n in NANOBOTS if n["id"] in ["NB01", "NB02", "NB03", "NB04", "NB05"]]
        elif strategy == "ds":
            # DeepSeek组: NB06-NB10
            candidates = [n for n in NANOBOTS if n["id"] in ["NB06", "NB07", "NB08", "NB09", "NB10"]]
        elif strategy == "random":
            candidates = random.sample(NANOBOTS, min(count, len(NANOBOTS)))
            return candidates
        else:
            # round_robin
            candidates = NANOBOTS
        
        # 选择成功率最高的节点
        sorted_nodes = sorted(candidates, 
                            key=lambda n: self.node_stats[n["id"]]["success"] - self.node_stats[n["id"]]["fail"],
                            reverse=True)
        
        return sorted_nodes[:count]
    
    def submit_task(self, task_id, prompt, node_id=None, strategy="auto", task_type=None, max_retries=2):
        """提交单个任务"""
        
        # 选择节点
        if node_id:
            nodes = [n for n in NANOBOTS if n["id"] == node_id]
            if not nodes:
                return {"task_id": task_id, "status": "failed", "error": f"Node {node_id} not found"}
        else:
            nodes = self.select_nodes(strategy, 1, task_type)
        
        node = nodes[0]
        
        # 执行并可能重试
        for attempt in range(max_retries + 1):
            start_time = time.time()
            
            success, result = self.relay.send_to_node(node["id"], prompt)
            duration = time.time() - start_time
            
            if success:
                # 更新统计
                self.node_stats[node["id"]]["success"] += 1
                
                # 记录任务
                task_record = {
                    "task_id": task_id,
                    "node_id": node["id"],
                    "prompt": prompt[:100],
                    "status": "success",
                    "duration": duration,
                    "attempts": attempt + 1,
                    "timestamp": datetime.now().isoformat()
                }
                self.task_history.append(task_record)
                
                return {
                    "task_id": task_id,
                    "status": "success",
                    "node_id": node["id"],
                    "result": result,
                    "duration": duration
                }
            else:
                # 更新失败统计
                self.node_stats[node["id"]]["fail"] += 1
                
                if attempt < max_retries:
                    time.sleep(1)  # 重试前等待
                    continue
                else:
                    # 最终失败
                    task_record = {
                        "task_id": task_id,
                        "node_id": node["id"],
                        "prompt": prompt[:100],
                        "status": "failed",
                        "error": result,
                        "attempts": attempt + 1,
                        "timestamp": datetime.now().isoformat()
                    }
                    self.task_history.append(task_record)
                    
                    return {
                        "task_id": task_id,
                        "status": "failed",
                        "node_id": node["id"],
                        "error": result,
                        "attempts": attempt + 1
                    }
    
    def submit_parallel(self, tasks, strategy="auto", max_workers=5):
        """并行提交多个任务
        
        tasks: list of {"task_id": str, "prompt": str, "task_type": str}
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self.submit_task,
                    task["task_id"],
                    task["prompt"],
                    task.get("node_id"),
                    strategy,
                    task.get("task_type"),
                    task.get("max_retries", 2)
                ): task["task_id"] for task in tasks
            }
            
            for future in as_completed(futures):
                task_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    status = "✅" if result["status"] == "success" else "❌"
                    print(f"  {status} Task {task_id}: {result.get('node_id', 'N/A')} ({result.get('duration', 0):.1f}s)")
                except Exception as e:
                    results.append({
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e)
                    })
                    print(f"  ❌ Task {task_id}: Exception - {e}")
        
        return results
    
    def show_stats(self):
        """显示节点统计"""
        print("=" * 60)
        print("📊 节点性能统计")
        print("=" * 60)
        
        for node_id, stats in self.node_stats.items():
            total = stats["success"] + stats["fail"]
            if total > 0:
                rate = stats["success"] / total * 100
                print(f"  {node_id}: {stats['success']}成功/{stats['fail']}失败 ({rate:.1f}%)")
            else:
                print(f"  {node_id}: 无数据")
        
        print("=" * 60)
        print(f"总任务数: {len(self.task_history)}")

def main():
    scheduler = TaskScheduler()
    
    if len(sys.argv) < 2:
        print("Task Scheduler")
        print("")
        print("Usage: scheduler.py <command> [options]")
        print("")
        print("Commands:")
        print("  submit <prompt> [--type TYPE] [--strategy STRATEGY]")
        print("  parallel <file.json>  从文件批量提交任务")
        print("  stats                 显示节点统计")
        print("")
        print("Types: quick, simple, fast, deep, complex, reasoning")
        print("Strategies: auto, step, ds, random, round_robin")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "submit":
        if len(sys.argv) < 3:
            print("Usage: submit <prompt>")
            sys.exit(1)
        
        prompt = sys.argv[2]
        task_type = None
        strategy = "auto"
        
        # 解析参数
        if "--type" in sys.argv:
            idx = sys.argv.index("--type")
            if idx + 1 < len(sys.argv):
                task_type = sys.argv[idx + 1]
        
        if "--strategy" in sys.argv:
            idx = sys.argv.index("--strategy")
            if idx + 1 < len(sys.argv):
                strategy = sys.argv[idx + 1]
        
        task_id = f"task_{int(time.time())}"
        print(f"🚀 提交任务 {task_id}...")
        print(f"   策略: {strategy}, 类型: {task_type or 'auto'}")
        
        result = scheduler.submit_task(task_id, prompt, strategy=strategy, task_type=task_type)
        
        if result["status"] == "success":
            print(f"✅ 完成 (节点: {result['node_id']}, 耗时: {result['duration']:.1f}s)")
            print(f"📤 结果: {result['result'][:100]}...")
        else:
            print(f"❌ 失败: {result['error']}")
    
    elif command == "stats":
        scheduler.show_stats()
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
