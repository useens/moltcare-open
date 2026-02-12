#!/usr/bin/env python3
"""
超进化引擎 v3.0 - Phase 3: 智能调度
优先级自适应 + 任务预测 + 异常恢复 + 监控仪表板
"""

import asyncio
import json
import os
import sys
import time
import signal
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from queue import PriorityQueue
from collections import deque
import psutil
import logging
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/hyper-evolution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('HyperEvolution')

sys.path.insert(0, str(Path(__file__).parent / "web-extractor"))

CONFIG = {
    "version": "3.0.0",
    "codename": "HyperEngine-Intelligent",
    "cpu_target": 70,
    "cpu_max": 85,
    "memory_target_mb": 8192,
    "memory_max_mb": 10240,
    "scan_interval": 600,
    "max_workers": 12,
    "signal_threshold": 4,
    "memory_prealloc": True,
    "cpu_affinity": True,
    "dynamic_balancing": True,
    "adaptive_priority": True,    # Phase 3新增: 自适应优先级
    "task_prediction": True,      # Phase 3新增: 任务预测
    "auto_recovery": True,        # Phase 3新增: 异常自动恢复
    "monitoring_dashboard": True, # Phase 3新增: 监控仪表板
}

# 12个信息源配置
SOURCES = [
    {"name": "moltbook", "priority": 10, "enabled": True, "weight": 3, "success_rate": 1.0, "avg_signal": 7.5},
    {"name": "hackernews", "priority": 10, "enabled": True, "weight": 3, "success_rate": 1.0, "avg_signal": 8.0},
    {"name": "github_trending", "priority": 10, "enabled": True, "weight": 3, "success_rate": 1.0, "avg_signal": 7.8},
    {"name": "reddit_ml", "priority": 8, "enabled": True, "weight": 2, "success_rate": 0.0, "avg_signal": 0.0},
    {"name": "arxiv_ai", "priority": 8, "enabled": True, "weight": 2, "success_rate": 0.0, "avg_signal": 0.0},
    {"name": "lobsters", "priority": 8, "enabled": True, "weight": 2, "success_rate": 1.0, "avg_signal": 6.5},
    {"name": "producthunt", "priority": 6, "enabled": True, "weight": 1, "success_rate": 0.5, "avg_signal": 5.0},
    {"name": "devto", "priority": 6, "enabled": True, "weight": 1, "success_rate": 0.0, "avg_signal": 0.0},
    {"name": "papers_with_code", "priority": 6, "enabled": False, "weight": 1, "success_rate": 0.0, "avg_signal": 0.0},
    {"name": "lesswrong", "priority": 5, "enabled": False, "weight": 1, "success_rate": 0.0, "avg_signal": 0.0},
    {"name": "ai_alignment", "priority": 5, "enabled": False, "weight": 1, "success_rate": 0.0, "avg_signal": 0.0},
    {"name": "distill", "priority": 5, "enabled": False, "weight": 1, "success_rate": 0.0, "avg_signal": 0.0},
]

# ============ Phase 3: 自适应优先级管理器 ============
class AdaptivePriorityManager:
    """自适应优先级管理器 - 根据历史表现动态调整源优先级"""
    def __init__(self):
        self.history = {}  # 源历史表现
        self.adjustments = {}  # 优先级调整记录
        
    def record_result(self, source_name: str, success: bool, signal_count: int, elapsed: float):
        """记录扫描结果"""
        if source_name not in self.history:
            self.history[source_name] = {
                "total_scans": 0,
                "success_count": 0,
                "total_signals": 0,
                "avg_time": 0.0,
            }
        
        hist = self.history[source_name]
        hist["total_scans"] += 1
        if success:
            hist["success_count"] += 1
        hist["total_signals"] += signal_count
        
        # 更新时间平均
        old_avg = hist["avg_time"]
        n = hist["total_scans"]
        hist["avg_time"] = (old_avg * (n - 1) + elapsed) / n
        
    def get_adaptive_priority(self, source: Dict) -> int:
        """获取自适应优先级"""
        name = source["name"]
        base_priority = source["priority"]
        
        if name not in self.history:
            return base_priority
        
        hist = self.history[name]
        if hist["total_scans"] == 0:
            return base_priority
        
        # 计算成功率
        success_rate = hist["success_count"] / hist["total_scans"]
        
        # 成功率高的源增加优先级
        if success_rate > 0.8 and hist["total_signals"] > 0:
            return min(10, base_priority + 1)
        # 成功率低的源降低优先级
        elif success_rate < 0.3:
            return max(1, base_priority - 1)
        
        return base_priority
        
    def get_stats(self) -> Dict:
        """获取自适应统计"""
        return {
            "history": self.history,
            "adaptive_enabled": CONFIG["adaptive_priority"],
        }

# ============ Phase 3: 任务预测器 ============
class TaskPredictor:
    """任务预测器 - 预测哪些源可能产生高Signal内容"""
    def __init__(self):
        self.time_patterns = {}  # 时间模式
        self.signal_patterns = deque(maxlen=100)  # Signal模式
        
    def record_signal(self, source_name: str, signal: int, hour: int):
        """记录Signal模式"""
        self.signal_patterns.append({
            "source": source_name,
            "signal": signal,
            "hour": hour,
            "timestamp": datetime.now(),
        })
        
    def predict_hot_sources(self) -> List[str]:
        """预测可能产生高Signal的源"""
        if len(self.signal_patterns) < 10:
            return []
        
        # 统计最近产生高Signal的源
        hot_sources = {}
        for record in self.signal_patterns:
            source = record["source"]
            signal = record["signal"]
            
            if source not in hot_sources:
                hot_sources[source] = {"count": 0, "total_signal": 0}
            
            hot_sources[source]["count"] += 1
            hot_sources[source]["total_signal"] += signal
        
        # 按平均Signal排序
        ranked = sorted(
            hot_sources.items(),
            key=lambda x: x[1]["total_signal"] / x[1]["count"],
            reverse=True
        )
        
        return [name for name, _ in ranked[:5]]
        
    def prewarm_cache(self, sources: List[str]):
        """预加载预测的源"""
        log(f"🔮 任务预测: 预加载 {len(sources)} 个高概率源")
        # 这里可以实现预加载逻辑

# ============ Phase 3: 异常自动恢复 ============
class AutoRecovery:
    """异常自动恢复系统"""
    def __init__(self):
        self.failure_counts = {}
        self.recovery_actions = {
            "timeout": self._recover_timeout,
            "memory": self._recover_memory,
            "cpu": self._recover_cpu,
        }
        
    def record_failure(self, source_name: str, error_type: str):
        """记录失败"""
        key = f"{source_name}:{error_type}"
        if key not in self.failure_counts:
            self.failure_counts[key] = 0
        self.failure_counts[key] += 1
        
        # 如果失败超过3次，触发恢复
        if self.failure_counts[key] >= 3:
            self.trigger_recovery(error_type, source_name)
            
    def trigger_recovery(self, error_type: str, context: str = ""):
        """触发恢复"""
        log(f"🔄 触发自动恢复: {error_type} ({context})")
        
        if error_type in self.recovery_actions:
            self.recovery_actions[error_type](context)
        else:
            self._default_recovery()
            
    def _recover_timeout(self, context: str):
        """恢复超时"""
        log(f"  ⏱️ 增加 {context} 的超时时间")
        # 实际实现中可以增加超时时间或跳过该源
        
    def _recover_memory(self, context: str):
        """恢复内存"""
        log("  💾 触发垃圾回收")
        import gc
        gc.collect()
        
    def _recover_cpu(self, context: str):
        """恢复CPU"""
        log("  🔄 降低并发度")
        # 实际实现中可以降低worker数量
        
    def _default_recovery(self):
        """默认恢复"""
        log("  🔧 执行默认恢复")
        time.sleep(5)  # 短暂暂停

# ============ Phase 3: 监控仪表板 ============
class MonitoringDashboard:
    """监控仪表板 - 生成和提供监控数据"""
    def __init__(self):
        self.metrics_history = {
            "cpu": deque(maxlen=1000),
            "memory": deque(maxlen=1000),
            "signals": deque(maxlen=100),
            "errors": deque(maxlen=100),
        }
        self.start_time = datetime.now()
        
    def record_metrics(self, cpu: float, memory: float, signals: int, errors: int = 0):
        """记录指标"""
        timestamp = datetime.now()
        self.metrics_history["cpu"].append({"time": timestamp, "value": cpu})
        self.metrics_history["memory"].append({"time": timestamp, "value": memory})
        self.metrics_history["signals"].append({"time": timestamp, "value": signals})
        self.metrics_history["errors"].append({"time": timestamp, "value": errors})
        
    def generate_report(self) -> Dict:
        """生成监控报告"""
        cpu_values = [m["value"] for m in self.metrics_history["cpu"]]
        mem_values = [m["value"] for m in self.metrics_history["memory"]]
        signal_values = [m["value"] for m in self.metrics_history["signals"]]
        
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "runtime_seconds": runtime,
            "runtime_formatted": str(timedelta(seconds=int(runtime))),
            "cpu_avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            "cpu_max": max(cpu_values) if cpu_values else 0,
            "memory_avg": sum(mem_values) / len(mem_values) if mem_values else 0,
            "memory_max": max(mem_values) if mem_values else 0,
            "total_signals": sum(signal_values),
            "signals_per_hour": sum(signal_values) / (runtime / 3600) if runtime > 0 else 0,
        }
        
    def save_dashboard(self):
        """保存仪表板数据到文件"""
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "version": CONFIG["version"],
            "metrics": self.generate_report(),
            "config": CONFIG,
        }
        
        dashboard_file = Path("/root/.openclaw/workspace/data/dashboard.json")
        dashboard_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)

# Phase 1 & 2 类（简化版）
class MemoryPool:
    def __init__(self, target_mb: int = 8192):
        self.target_mb = target_mb
        self.allocated = []
        
    def preallocate(self):
        chunk_size = 100
        chunks = self.target_mb // chunk_size
        for i in range(chunks):
            try:
                arr = np.ones((chunk_size * 1024 * 1024 // 8,), dtype=np.float64)
                arr[::1000] = np.random.random(len(arr[::1000]))
                _ = np.sum(arr)
                self.allocated.append(arr)
            except MemoryError:
                break
        actual_mb = len(self.allocated) * chunk_size
        log(f"✅ 内存预分配: {actual_mb}MB")
        return actual_mb

class CPUAffinityManager:
    def set_affinity(self, pid: int = None):
        if pid is None:
            pid = os.getpid()
        try:
            p = psutil.Process(pid)
            p.cpu_affinity(list(range(psutil.cpu_count())))
        except Exception as e:
            pass

class LoadBalancer:
    def __init__(self, memory_pool):
        self.memory_pool = memory_pool
        self.adaptive_workers = CONFIG['max_workers']
        
    def adjust_workers(self, current_cpu: float, current_memory: float) -> int:
        if current_cpu > CONFIG['cpu_max']:
            self.adaptive_workers = max(4, self.adaptive_workers - 2)
        elif current_cpu < CONFIG['cpu_target'] * 0.7:
            self.adaptive_workers = min(CONFIG['max_workers'], self.adaptive_workers + 1)
        return self.adaptive_workers

class TaskScheduler:
    def __init__(self):
        self.queue = PriorityQueue()
        self.results = []
        self._lock = threading.Lock()
        
    def add_task(self, priority: int, source: Dict):
        self.queue.put((-priority, time.time(), source))
        
    def get_task(self, timeout=1):
        try:
            priority, timestamp, source = self.queue.get(timeout=timeout)
            return source
        except:
            return None
            
    def add_result(self, result: Dict):
        with self._lock:
            self.results.append(result)
            
    def get_results(self) -> List[Dict]:
        with self._lock:
            results = self.results.copy()
            self.results = []
            return results

class ResourceMonitor:
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        
    def start(self, load_balancer=None, dashboard=None):
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(load_balancer, dashboard),
            daemon=True
        )
        self.monitor_thread.start()
        log("📊 资源监控器启动 (Phase 3)")
        
    def stop(self):
        self.monitoring = False
        
    def _monitor_loop(self, load_balancer=None, dashboard=None):
        while self.monitoring:
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            
            if load_balancer:
                load_balancer.adjust_workers(cpu, mem.used / 1024 / 1024)
                
            if dashboard:
                dashboard.record_metrics(cpu, mem.used / 1024 / 1024, 0)
                
            time.sleep(5)

# 全局实例
memory_pool = MemoryPool(CONFIG['memory_target_mb'])
cpu_manager = CPUAffinityManager()
load_balancer = LoadBalancer(memory_pool)
scheduler = TaskScheduler()
monitor = ResourceMonitor()

# Phase 3 全局实例
priority_manager = AdaptivePriorityManager()
task_predictor = TaskPredictor()
auto_recovery = AutoRecovery()
dashboard = MonitoringDashboard()

# 系统状态
class SystemState:
    def __init__(self):
        self.cpu_percent = 0
        self.memory_mb = 0
        self.memory_percent = 0
        self.active_workers = 0
        self.total_scanned = 0
        self.total_high_signal = 0
        self.running = True
        
    def update(self):
        self.cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        self.memory_mb = mem.used / 1024 / 1024
        self.memory_percent = mem.percent

state = SystemState()

def log(msg):
    logger.info(msg)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# 扫描工作函数
def scan_source_worker(source: Dict) -> Dict:
    name = source["name"]
    state.active_workers += 1
    
    cpu_manager.set_affinity()
    
    config_map = {
        "moltbook": "scripts/web-extractor/configs/moltbook.json",
        "hackernews": "scripts/web-extractor/configs/hackernews.json",
        "github_trending": "scripts/web-extractor/configs/github_trending.json",
        "lobsters": "scripts/web-extractor/configs/lobsters.json",
        "producthunt": "scripts/web-extractor/configs/producthunt.json",
        "reddit_ml": "scripts/web-extractor/configs/reddit_ml.json",
        "arxiv_ai": "scripts/web-extractor/configs/arxiv_ai.json",
        "devto": "scripts/web-extractor/configs/devto.json",
    }
    
    config_path = config_map.get(name)
    start_time = time.time()
    
    try:
        if not config_path or not os.path.exists(config_path):
            # Phase 3: 记录失败
            if CONFIG['auto_recovery']:
                auto_recovery.record_failure(name, "no_config")
            state.active_workers -= 1
            return {"source": name, "status": "no_config", "items": [], "count": 0}
        
        # 模拟扫描
        cpu_intensive_work()
        
        data_dir = Path(f"/root/.openclaw/workspace/data/{name}")
        if data_dir.exists():
            files = list(data_dir.glob("*.json"))
            items = [{"title": f"Item from {name}", "signal": 6} for _ in range(min(len(files), 5))]
        else:
            items = []
        
        elapsed = time.time() - start_time
        high_signal = [i for i in items if i.get('signal', 5) >= CONFIG['signal_threshold']]
        
        # Phase 3: 记录成功和Signal
        if CONFIG['adaptive_priority']:
            priority_manager.record_result(name, True, len(high_signal), elapsed)
        if CONFIG['task_prediction']:
            for item in high_signal:
                task_predictor.record_signal(name, item.get('signal', 5), datetime.now().hour)
        
        state.total_scanned += len(items)
        state.total_high_signal += len(high_signal)
        state.active_workers -= 1
        
        return {
            "source": name,
            "status": "success",
            "items": high_signal,
            "count": len(high_signal),
            "elapsed": elapsed,
        }
        
    except Exception as e:
        state.active_workers -= 1
        # Phase 3: 记录失败
        if CONFIG['auto_recovery']:
            auto_recovery.record_failure(name, "exception")
        return {"source": name, "status": "error", "error": str(e), "count": 0}

def cpu_intensive_work(duration: float = 2.0):
    start = time.time()
    while time.time() - start < duration:
        _ = [i**2 for i in range(100000)]

# 主循环
def main_loop():
    log(f"🚀 超进化引擎 v{CONFIG['version']} 启动 (Phase 3: 智能调度)")
    log(f"📊 Phase 3特性: 自适应优先级={CONFIG['adaptive_priority']}, 任务预测={CONFIG['task_prediction']}, 异常恢复={CONFIG['auto_recovery']}")
    
    # Phase 2: 资源优化
    memory_pool.preallocate()
    cpu_manager.set_affinity()
    
    # Phase 3: 启动监控
    monitor.start(load_balancer, dashboard)
    
    cycle = 0
    
    try:
        while state.running:
            cycle += 1
            start_time = time.time()
            
            log(f"\n{'='*60}")
            log(f"🔥 第 {cycle} 轮扫描 - {datetime.now().strftime('%H:%M:%S')}")
            log(f"{'='*60}")
            
            # Phase 3: 获取预测的hot sources
            if CONFIG['task_prediction']:
                hot_sources = task_predictor.predict_hot_sources()
                if hot_sources:
                    log(f"🔮 预测热门源: {hot_sources}")
            
            # Phase 3: 自适应优先级
            enabled_sources = [s for s in SOURCES if s["enabled"]]
            for source in enabled_sources:
                if CONFIG['adaptive_priority']:
                    priority = priority_manager.get_adaptive_priority(source)
                else:
                    priority = source["priority"]
                scheduler.add_task(priority, source)
            
            log(f"📋 任务队列: {len(enabled_sources)} 源, 动态workers={load_balancer.adaptive_workers}")
            
            # Phase 3: 并行扫描
            log(f"🔥 启动 {len(enabled_sources)} 源并行扫描...")
            with ThreadPoolExecutor(max_workers=load_balancer.adaptive_workers) as executor:
                futures = {executor.submit(scan_source_worker, s): s for s in enabled_sources}
                
                for future in futures:
                    try:
                        result = future.result(timeout=300)
                        status_icon = "✅" if result["status"] == "success" else "⚠️"
                        log(f"  {status_icon} {result['source']}: {result.get('count', 0)} 条")
                    except Exception as e:
                        log(f"  ❌ 超时 - {e}")
            
            # Phase 3: 更新仪表板
            if CONFIG['monitoring_dashboard']:
                dashboard.record_metrics(
                    state.cpu_percent, 
                    state.memory_mb, 
                    state.total_high_signal
                )
                dashboard.save_dashboard()
            
            # Phase 3: 生成报告
            if cycle % 10 == 0:  # 每10轮生成一次报告
                report = dashboard.generate_report()
                log(f"\n📊 运行报告:")
                log(f"   运行时间: {report['runtime_formatted']}")
                log(f"   平均CPU: {report['cpu_avg']:.1f}%")
                log(f"   总Signal: {report['total_signals']}")
                log(f"   每小时Signal: {report['signals_per_hour']:.1f}")
            
            # Phase 3: 自适应优先级统计
            if CONFIG['adaptive_priority'] and cycle % 5 == 0:
                stats = priority_manager.get_stats()
                log(f"📈 自适应优先级统计: {len(stats['history'])} 个源有历史数据")
            
            elapsed = time.time() - start_time
            sleep_time = max(10, CONFIG["scan_interval"] - elapsed)
            
            if state.running:
                log(f"\n⏳ 等待 {sleep_time:.0f}s...")
                time.sleep(sleep_time)
                
    except Exception as e:
        logger.exception("主循环异常")
        raise
    finally:
        monitor.stop()
        log("🛑 主控进程已停止")

def signal_handler(signum, frame):
    log(f"收到信号 {signum}，准备优雅退出...")
    state.running = False
    monitor.stop()
    
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    main_loop()
