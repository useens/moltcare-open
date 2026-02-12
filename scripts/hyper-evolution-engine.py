#!/usr/bin/env python3
"""
超进化引擎 v1.0 - Hyper Evolution Engine
持续后台进程，真正的并行执行，极限资源利用

架构:
- 主控进程 (Master) - 任务调度、资源监控
- 工作进程池 (Worker Pool) - 12源并行扫描
- 内存管理器 (Memory Manager) - 8GB预分配
- 监控器 (Monitor) - 实时CPU/内存监控
"""

import asyncio
import json
import multiprocessing as mp
import os
import signal
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from queue import PriorityQueue
from typing import Dict, List, Optional, Any
import threading
import psutil

# 配置
CONFIG = {
    "version": "1.0.0",
    "codename": "HyperEngine",
    
    # 资源目标
    "cpu_target_percent": 70,
    "cpu_max_percent": 85,
    "memory_target_mb": 7000,
    "memory_max_mb": 8192,
    
    # 并行配置
    "max_workers": 30,
    "source_workers": 12,  # 12个信息源并行
    "io_workers": 8,
    
    # 扫描配置
    "scan_interval_seconds": 600,  # 10分钟
    "sources": [
        {"name": "Moltbook", "priority": 10, "url": "https://www.moltbook.com/?sort=hot"},
        {"name": "HackerNews", "priority": 10, "url": "https://news.ycombinator.com/"},
        {"name": "GitHub_Trending", "priority": 10, "url": "https://github.com/trending"},
        {"name": "Reddit_ML", "priority": 8, "url": "https://www.reddit.com/r/MachineLearning/hot/"},
        {"name": "arXiv_AI", "priority": 8, "url": "http://arxiv.org/rss/cs.AI"},
        {"name": "PapersWithCode", "priority": 8, "url": "https://paperswithcode.com/"},
        {"name": "Lobsters", "priority": 6, "url": "https://lobste.rs/"},
        {"name": "ProductHunt", "priority": 6, "url": "https://www.producthunt.com/"},
        {"name": "DevTo", "priority": 6, "url": "https://dev.to/t/ai"},
        {"name": "LessWrong", "priority": 5, "url": "https://www.lesswrong.com/"},
        {"name": "AIAlignment", "priority": 5, "url": "https://alignmentforum.org/"},
        {"name": "Distill", "priority": 5, "url": "https://distill.pub/"},
    ],
    
    # 监控配置
    "monitor_interval": 5,  # 每5秒监控一次
    "adaptive_scaling": True,
}

@dataclass
class Task:
    """任务定义"""
    id: str
    name: str
    priority: int
    source: str
    func: callable = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __lt__(self, other):
        return self.priority > other.priority  # 高优先级先执行

class ResourceMonitor:
    """资源监控器 - 实时监控CPU/内存"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cpu_usage = 0.0
        self.memory_usage_mb = 0
        self.memory_percent = 0.0
        self.running = True
        self.monitor_thread = None
        
    def start(self):
        """启动监控线程"""
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print(f"[{datetime.now()}] 资源监控器启动")
        
    def stop(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
            
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # CPU使用率
                self.cpu_usage = psutil.cpu_percent(interval=1)
                
                # 内存使用
                mem = psutil.virtual_memory()
                self.memory_usage_mb = mem.used / 1024 / 1024
                self.memory_percent = mem.percent
                
                # 自适应调整 (如果启用)
                if self.config.get("adaptive_scaling"):
                    self._adaptive_adjust()
                    
            except Exception as e:
                print(f"[{datetime.now()}] 监控错误: {e}")
                
            time.sleep(self.config["monitor_interval"])
    
    def _adaptive_adjust(self):
        """自适应调整"""
        # CPU过低，可以增加任务
        if self.cpu_usage < self.config["cpu_target_percent"] - 20:
            pass  # 信号给调度器增加任务
            
        # CPU过高，需要降低负载
        if self.cpu_usage > self.config["cpu_max_percent"]:
            print(f"[{datetime.now()}] ⚠️ CPU过高 ({self.cpu_usage}%), 降低负载")
            
        # 内存过高
        if self.memory_usage_mb > self.config["memory_max_mb"]:
            print(f"[{datetime.now()}] ⚠️ 内存过高 ({self.memory_usage_mb:.0f}MB), 触发GC")
            import gc
            gc.collect()
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            "cpu_percent": self.cpu_usage,
            "memory_mb": self.memory_usage_mb,
            "memory_percent": self.memory_percent,
            "timestamp": datetime.now().isoformat(),
        }

class MemoryManager:
    """内存管理器 - 预分配和优化"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cache = {}
        self.max_cache_size = 1000
        
    def preallocate(self):
        """预分配内存"""
        # 预分配大的数据结构
        target_mb = self.config["memory_target_mb"]
        print(f"[{datetime.now()}] 预分配 {target_mb}MB 内存...")
        
        # 这里可以预加载常用数据到内存
        # 例如：向量索引、知识图谱等
        
    def cache_set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        if len(self.cache) >= self.max_cache_size:
            # LRU淘汰
            oldest_key = min(self.cache, key=lambda k: self.cache[k]["time"])
            del self.cache[oldest_key]
            
        self.cache[key] = {
            "value": value,
            "time": time.time(),
            "ttl": ttl,
        }
        
    def cache_get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item["time"] < item["ttl"]:
                return item["value"]
            else:
                del self.cache[key]
        return None

class SourceScanner:
    """信息源扫描器 - 使用Playwright并行扫描"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.results = {}
        
    async def scan_source(self, source: Dict) -> Dict:
        """扫描单个信息源"""
        name = source["name"]
        url = source["url"]
        
        print(f"[{datetime.now()}] 🔍 扫描: {name}")
        
        try:
            # 这里调用实际的扫描逻辑
            # 例如：使用Playwright提取内容
            
            # 模拟扫描结果
            result = {
                "source": name,
                "url": url,
                "status": "success",
                "items_found": 0,
                "high_signal_items": [],
                "timestamp": datetime.now().isoformat(),
            }
            
            # 实际实现时，这里调用:
            # from scripts.web_extractor.deep_learning_extractor import DeepLearningExtractor
            # extractor = DeepLearningExtractor(f"configs/{name.lower()}.json")
            # items = await extractor.collect_with_deep_learning()
            
            return result
            
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 扫描失败 {name}: {e}")
            return {
                "source": name,
                "status": "error",
                "error": str(e),
            }
    
    async def scan_all_sources(self) -> List[Dict]:
        """并行扫描所有信息源"""
        sources = self.config["sources"]
        
        # 使用asyncio并发扫描所有源
        tasks = [self.scan_source(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤异常
        valid_results = []
        for r in results:
            if isinstance(r, Exception):
                print(f"[{datetime.now()}] ❌ 扫描异常: {r}")
            else:
                valid_results.append(r)
                
        return valid_results

class TaskScheduler:
    """任务调度器 - 优先级队列 + 动态调度"""
    
    def __init__(self, config: Dict, monitor: ResourceMonitor):
        self.config = config
        self.monitor = monitor
        self.task_queue = PriorityQueue()
        self.running_tasks = {}
        self.completed_tasks = []
        self.executor = ThreadPoolExecutor(max_workers=config["max_workers"])
        
    def submit_task(self, task: Task):
        """提交任务"""
        self.task_queue.put(task)
        print(f"[{datetime.now()}] 📋 任务入队: {task.name} (优先级{task.priority})")
        
    async def process_tasks(self):
        """处理任务队列"""
        while True:
            try:
                # 检查资源状态
                status = self.monitor.get_status()
                
                # 如果资源充足，执行任务
                if status["cpu_percent"] < self.config["cpu_max_percent"]:
                    if not self.task_queue.empty():
                        task = self.task_queue.get()
                        
                        # 提交到线程池执行
                        future = self.executor.submit(self._execute_task, task)
                        self.running_tasks[task.id] = future
                        
                # 清理完成的任务
                self._cleanup_completed()
                
                await asyncio.sleep(0.1)  # 100ms调度周期
                
            except Exception as e:
                print(f"[{datetime.now()}] ❌ 调度错误: {e}")
                await asyncio.sleep(1)
    
    def _execute_task(self, task: Task):
        """执行任务"""
        print(f"[{datetime.now()}] 🚀 执行任务: {task.name}")
        
        try:
            if task.func:
                result = task.func(*task.args, **task.kwargs)
            else:
                result = None
                
            self.completed_tasks.append({
                "task": task,
                "result": result,
                "completed_at": datetime.now(),
            })
            
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 任务失败 {task.name}: {e}")
            
    def _cleanup_completed(self):
        """清理完成的任务"""
        completed_ids = []
        for task_id, future in self.running_tasks.items():
            if future.done():
                completed_ids.append(task_id)
                
        for task_id in completed_ids:
            del self.running_tasks[task_id]

class HyperEvolutionEngine:
    """超进化引擎主控"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.monitor = ResourceMonitor(config)
        self.memory_manager = MemoryManager(config)
        self.scanner = SourceScanner(config)
        self.scheduler = TaskScheduler(config, self.monitor)
        self.running = True
        self.cycle_count = 0
        
        # 信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """信号处理"""
        print(f"\n[{datetime.now()}] 🛑 收到信号 {signum}, 优雅停止...")
        self.running = False
        
    def start(self):
        """启动引擎"""
        print(f"\n{'='*60}")
        print(f"🌌 超进化引擎 v{self.config['version']} - {self.config['codename']}")
        print(f"{'='*60}")
        print(f"启动时间: {datetime.now()}")
        print(f"CPU目标: {self.config['cpu_target_percent']}%")
        print(f"内存目标: {self.config['memory_target_mb']}MB")
        print(f"并行工作器: {self.config['max_workers']}")
        print(f"扫描源数: {len(self.config['sources'])}")
        print(f"扫描间隔: {self.config['scan_interval_seconds']}秒")
        print(f"{'='*60}\n")
        
        # 启动组件
        self.monitor.start()
        self.memory_manager.preallocate()
        
        # 启动主循环
        asyncio.run(self._main_loop())
        
    async def _main_loop(self):
        """主循环"""
        # 启动任务调度器
        scheduler_task = asyncio.create_task(self.scheduler.process_tasks())
        
        while self.running:
            try:
                self.cycle_count += 1
                cycle_start = time.time()
                
                print(f"\n[{datetime.now()}] 🔄 第 {self.cycle_count} 轮超进化开始")
                
                # 1. 并行扫描12个信息源
                print(f"[{datetime.now()}] 📡 并行扫描 {len(self.config['sources'])} 个信息源...")
                scan_results = await self.scanner.scan_all_sources()
                
                # 2. 提交后续处理任务
                for result in scan_results:
                    if result.get("status") == "success":
                        task = Task(
                            id=f"process_{result['source']}_{self.cycle_count}",
                            name=f"处理 {result['source']}",
                            priority=5,
                            source=result["source"],
                        )
                        self.scheduler.submit_task(task)
                
                # 3. 等待本轮完成或进入下一轮
                cycle_duration = time.time() - cycle_start
                wait_time = self.config["scan_interval_seconds"] - cycle_duration
                
                if wait_time > 0:
                    print(f"[{datetime.now()}] ⏱️ 本轮耗时 {cycle_duration:.1f}s, 等待 {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"[{datetime.now()}] ⚡ 本轮耗时 {cycle_duration:.1f}s, 超过间隔")
                    
                # 4. 输出状态报告
                status = self.monitor.get_status()
                print(f"[{datetime.now()}] 📊 状态: CPU {status['cpu_percent']:.1f}% | 内存 {status['memory_mb']:.0f}MB")
                
            except Exception as e:
                print(f"[{datetime.now()}] ❌ 主循环错误: {e}")
                await asyncio.sleep(5)
        
        # 优雅关闭
        print(f"\n[{datetime.now()}] 🛑 停止超进化引擎...")
        self.monitor.stop()
        self.scheduler.executor.shutdown(wait=True)
        
        print(f"[{datetime.now()}] ✅ 引擎已停止，总循环: {self.cycle_count}")
        
def main():
    """主函数"""
    engine = HyperEvolutionEngine(CONFIG)
    engine.start()

if __name__ == "__main__":
    main()
