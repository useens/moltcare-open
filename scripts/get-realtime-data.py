#!/usr/bin/env python3
"""
超进化引擎实时数据获取器
用于报告生成时获取最新、准确的数据
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

def get_hyper_evolution_realtime_data():
    """获取超进化引擎实时数据"""
    data = {
        "version": "4.6.0",
        "codename": "HyperEngine-AdaptiveFreq",
        "timestamp": datetime.now().isoformat(),
        "service_status": "unknown",
        "uptime_seconds": 0,
        "scan_count": 0,
        "high_signal_total": 0,
        "avg_discovery_rate": 0,
        "current_interval": 600
    }
    
    # 1. 检查服务状态
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "hyper-evolution"],
            capture_output=True, text=True, timeout=5
        )
        data["service_status"] = result.stdout.strip()
    except:
        pass
    
    # 2. 读取自适应频率历史记录
    try:
        freq_file = Path("memory/adaptive_freq.json")
        if freq_file.exists():
            with open(freq_file) as f:
                freq_data = json.load(f)
                history = freq_data.get("history", [])
                
                if history:
                    # 计算统计数据
                    data["scan_count"] = len(history)
                    data["high_signal_total"] = sum(h.get("high_signal", 0) for h in history)
                    
                    total_scanned = sum(h.get("total", 0) for h in history)
                    if total_scanned > 0:
                        data["avg_discovery_rate"] = round(data["high_signal_total"] / total_scanned * 100, 1)
                    
                    # 当前间隔
                    data["current_interval"] = history[-1].get("interval_used", 600)
                    
                    # 计算运行时间 (从第一条记录开始)
                    first_scan = history[0].get("timestamp", 0)
                    if first_scan:
                        data["uptime_seconds"] = int(datetime.now().timestamp() - first_scan)
    except Exception as e:
        print(f"读取频率历史失败: {e}")
    
    return data


def get_system_realtime_data():
    """获取系统实时数据"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "cpu_load": [],
        "memory": {},
        "disk": {}
    }
    
    # CPU负载
    try:
        result = subprocess.run(
            ["uptime"],
            capture_output=True, text=True, timeout=5
        )
        # 解析负载
        load_str = result.stdout.split("load average:")[-1].strip()
        data["cpu_load"] = [float(x.strip()) for x in load_str.split(",")]
    except:
        pass
    
    # 内存
    try:
        result = subprocess.run(
            ["free", "-m"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.split("\n")
        for line in lines:
            if line.startswith("Mem:"):
                parts = line.split()
                data["memory"] = {
                    "total_mb": int(parts[1]),
                    "used_mb": int(parts[2]),
                    "free_mb": int(parts[3])
                }
                break
    except:
        pass
    
    # 磁盘
    try:
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            data["disk"] = {
                "size": parts[1],
                "used": parts[2],
                "available": parts[3],
                "usage_percent": parts[4]
            }
    except:
        pass
    
    return data


if __name__ == "__main__":
    print("🔍 获取超进化引擎实时数据...")
    hyper_data = get_hyper_evolution_realtime_data()
    print(f"\n超进化引擎 v{hyper_data['version']}:")
    print(f"  服务状态: {hyper_data['service_status']}")
    print(f"  扫描次数: {hyper_data['scan_count']}")
    print(f"  高Signal: {hyper_data['high_signal_total']}")
    print(f"  发现率: {hyper_data['avg_discovery_rate']}%")
    print(f"  当前间隔: {hyper_data['current_interval']}秒")
    
    print("\n🔍 获取系统实时数据...")
    sys_data = get_system_realtime_data()
    print(f"\n系统状态:")
    print(f"  CPU负载: {sys_data['cpu_load']}")
    print(f"  内存: {sys_data['memory']}")
    print(f"  磁盘: {sys_data['disk']}")
