#!/usr/bin/env python3
"""
森森状态快照采集器
负责收集系统完整状态并生成标准化快照
"""
import os
import sys
import json
import time
import uuid
import platform
import subprocess
import psutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

@dataclass
class SnapshotConfig:
    """快照采集配置"""
    snapshot_type: str = "check"  # baseline, check, pre_shutdown, post_startup, manual
    parent_id: Optional[str] = None
    include_io_stats: bool = False  # IO统计可能耗时
    timeout_sec: int = 30
    reason: Optional[str] = None

class SnapshotCollector:
    """状态快照采集器"""
    
    VERSION = "1.0.0"
    
    def __init__(self, config: SnapshotConfig = None):
        self.config = config or SnapshotConfig()
        self.snapshot_id = str(uuid.uuid4())
        
    def collect(self) -> Dict[str, Any]:
        """采集完整状态快照"""
        snapshot = {
            "version": self.VERSION,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "hostname": self._get_hostname(),
            "session_id": self._get_session_id(),
            "snapshot_id": self.snapshot_id,
            "snapshot_type": self.config.snapshot_type,
            "parent_snapshot_id": self.config.parent_id,
            "system": self._collect_system_info(),
            "resources": self._collect_resources(),
            "cron": self._collect_cron_info(),
            "skills": self._collect_skills_info(),
            "connections": self._collect_connections(),
            "metadata": {
                "reason": self.config.reason,
                "source": "snapshot_collector",
                "drift_detected": False,
                "drift_details": None
            }
        }
        return snapshot
    
    def _get_hostname(self) -> str:
        """获取主机名"""
        return platform.node()
    
    def _get_session_id(self) -> str:
        """获取OpenClaw会话ID"""
        # 尝试从环境变量获取
        session_id = os.environ.get('OPENCLAW_SESSION_ID') or os.environ.get('SESSION_ID')
        if not session_id:
            # 生成临时会话ID
            session_id = f"temp-{self.snapshot_id[:8]}"
        return session_id
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """采集系统信息"""
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        return {
            "platform": platform.system(),
            "arch": platform.machine(),
            "release": platform.release(),
            "kernel_version": platform.version(),
            "uptime": round(uptime, 2),
            "load_average": list(os.getloadavg()) if hasattr(os, 'getloadavg') else [0.0, 0.0, 0.0],
            "hostname": platform.node(),
            "timezone": time.tzname[0] if time.tzname else "UTC"
        }
    
    def _collect_resources(self) -> Dict[str, Any]:
        """采集资源使用情况"""
        # CPU
        cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # 尝试获取CPU温度（仅部分系统支持）
        cpu_temp = None
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        cpu_temp = entries[0].current
                        break
        except:
            pass
        
        # 内存
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # 磁盘
        partitions = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    "mount": part.mountpoint,
                    "filesystem": part.fstype,
                    "device": part.device,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "usage_percent": round(usage.percent, 2)
                })
            except (PermissionError, OSError):
                continue
        
        return {
            "cpu": {
                "usage_percent": round(cpu_percent, 2),
                "count": cpu_count,
                "count_logical": cpu_count_logical,
                "temperature": cpu_temp
            },
            "memory": {
                "total_bytes": mem.total,
                "available_bytes": mem.available,
                "used_bytes": mem.used,
                "free_bytes": mem.free,
                "buffers_bytes": getattr(mem, 'buffers', 0),
                "cached_bytes": getattr(mem, 'cached', 0),
                "usage_percent": round(mem.percent, 2),
                "swap": {
                    "total_bytes": swap.total,
                    "used_bytes": swap.used,
                    "free_bytes": swap.free
                }
            },
            "disk": {
                "partitions": partitions
            }
        }
    
    def _collect_cron_info(self) -> Dict[str, Any]:
        """采集Cron任务信息"""
        jobs = []
        
        # 尝试读取crontab
        try:
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 简单解析: 前5个字段是schedule，后面是command
                        parts = line.split()
                        if len(parts) >= 6:
                            schedule = ' '.join(parts[:5])
                            command = ' '.join(parts[5:])
                            jobs.append({
                                "id": f"crontab-{i}",
                                "name": f"User cron job {i}",
                                "schedule": schedule,
                                "command": command,
                                "enabled": True,
                                "last_run": None,
                                "next_run": None,
                                "status": "idle",
                                "last_exit_code": None,
                                "run_count": 0
                            })
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            pass
        
        # 检查系统cron目录
        cron_dirs = ['/etc/cron.d', '/etc/cron.hourly', '/etc/cron.daily', 
                     '/etc/cron.weekly', '/etc/cron.monthly']
        for cron_dir in cron_dirs:
            if os.path.isdir(cron_dir):
                try:
                    for item in os.listdir(cron_dir):
                        item_path = os.path.join(cron_dir, item)
                        if os.path.isfile(item_path) and not item.startswith('.'):
                            jobs.append({
                                "id": f"system-{item}",
                                "name": f"System cron: {item}",
                                "schedule": "see script",
                                "command": item_path,
                                "enabled": True,
                                "last_run": None,
                                "status": "idle",
                                "run_count": 0
                            })
                except PermissionError:
                    pass
