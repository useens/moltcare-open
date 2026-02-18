"""
数据收集器 -收集系统各维度数据
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
import sqlite3
from core import event_bus, StateManager, Event

DB_PATH = Path("/root/.openclaw/workspace/evolution/data/evolution.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class BaseCollector(ABC):
    """收集器基类"""
    def __init__(self, name: str, interval_seconds: int = 300):
        self.name = name
        self.interval = interval_seconds
        self.state = StateManager()

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """收集数据"""
        pass

    def store(self, data: Dict[str, Any]):
        """存储到数据库"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 创建表（首次）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collector TEXT,
                timestamp TEXT,
                data TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                source TEXT,
                timestamp TEXT,
                data TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                trigger TEXT,
                strategy TEXT,
                confidence REAL,
                action TEXT,
                status TEXT,
                before_state TEXT,
                after_state TEXT,
                rollback_reason TEXT
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()

class PerformanceCollector(BaseCollector):
    """性能指标收集：成本、响应时间、token使用"""
    def collect(self) -> Dict[str, Any]:
        # 从 unified-monitor 或其他来源获取数据
        # 这里返回模拟数据（实际应从 OpenClaw API 或日志解析）
        return {
            "timestamp": datetime.now().isoformat(),
            "costs": {
                "step_per_hour": 0.0,  # 需解析实际
                "k2p5_per_hour": 0.0
            },
            "tokens": {
                "input_last_6h": 0,
                "output_last_6h": 0,
                "cache_hit_rate": 0.0
            },
            "latency": {
                "avg_response_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0
            }
        }

class BehaviorCollector(BaseCollector):
    """行为数据：模型选择、用户反馈、路由准确率"""
    def collect(self) -> Dict[str, Any]:
        # 从 sessions.json 和用户反馈收集
        return {
            "timestamp": datetime.now().isoformat(),
            "model_usage": {
                "step_count": 0,
                "k2p5_count": 0,
                "nvidia_kimi_count": 0,
                "total": 0
            },
            "user_feedback": {
                "approvals": 0,
                "rejections": 0,
                "auto_accepted": 0
            },
            "routing_accuracy": {
                "correct": 0,
                "incorrect": 0,
                "accuracy_rate": 0.0
            }
        }

class SystemHealthCollector(BaseCollector):
    """系统健康：存储、内存、cron、git"""
    def collect(self) -> Dict[str, Any]:
        import psutil
        import subprocess

        # 磁盘使用
        disk = psutil.disk_usage("/root/.openclaw/workspace")
        storage_pct = (disk.used / disk.total) * 100

        # 内存
        mem = psutil.virtual_memory()
        mem_pct = mem.percent

        # cron 状态
        cron_status = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True
        ).returncode == 0

        # git 状态
        git_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd="/root/.openclaw/workspace",
            capture_output=True, text=True
        )
        git_dirty = bool(git_result.stdout.strip())

        return {
            "timestamp": datetime.now().isoformat(),
            "storage": {
                "used_gb": disk.used / 1e9,
                "total_gb": disk.total / 1e9,
                "usage_pct": storage_pct,
                "status": "healthy" if storage_pct < 80 else "warning"
            },
            "memory": {
                "used_gb": mem.used / 1e9,
                "total_gb": mem.total / 1e9,
                "usage_pct": mem_pct,
                "status": "healthy" if mem_pct < 85 else "warning"
            },
            "cron": {
                "enabled": cron_status,
                "jobs_count": 0  # TODO: parse count
            },
            "git": {
                "dirty": git_dirty,
                "status": "warning" if git_dirty else "healthy"
            }
        }

class ExternalIntelCollector(BaseCollector):
    """外部情报：新模型、API变更、成本变化"""
    def collect(self) -> Dict[str, Any]:
        # TODO: 从 Brave Search 或 RSS 抓取
        return {
            "timestamp": datetime.now().isoformat(),
            "new_models": [],
            "api_changes": [],
            "cost_updates": []
        }

# 收集器工厂
COLLECTORS = {
    "performance": PerformanceCollector("performance", 300),
    "behavior": BehaviorCollector("behavior", 300),
    "system": SystemHealthCollector("system", 300),
    "external": ExternalIntelCollector("external", 3600)
}

def run_all_collectors():
    """运行所有收集器"""
    for collector in COLLECTORS.values():
        try:
            data = collector.collect()
            # 存储到数据库
            collector.store(data)
            # 发布事件
            event_bus.publish(Event(
                type="data.collected",
                source=collector.name,
                timestamp=datetime.now(),
                data=data
            ))
        except Exception as e:
            print(f"[Collector] {collector.name} error: {e}")

if __name__ == "__main__":
    run_all_collectors()
    print("✅ All collectors executed")
