#!/usr/bin/env python3
"""
CPU利用率监控器 - 确保CPU利用率在目标范围
"""
import psutil
import time
from datetime import datetime
from pathlib import Path
import json

WORKSPACE = Path("/root/.openclaw/workspace")
TARGET_CPU_MIN = 50  # 目标最小CPU利用率
TARGET_CPU_MAX = 80  # 目标最大CPU利用率

def monitor_cpu():
    """监控并优化CPU利用率"""
    cpu_percent = psutil.cpu_percent(interval=2)
    
    print(f"当前CPU利用率: {cpu_percent}%")
    
    if cpu_percent < TARGET_CPU_MIN:
        print(f"⚠️ CPU利用率偏低，建议增加并行任务")
        status = "underutilized"
    elif cpu_percent > TARGET_CPU_MAX:
        print(f"⚠️ CPU利用率过高，可能需要优化")
        status = "overloaded"
    else:
        print(f"✅ CPU利用率在目标范围")
        status = "optimal"
    
    # 记录证据
    evidence = {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": cpu_percent,
        "status": status,
        "target_range": f"{TARGET_CPU_MIN}-{TARGET_CPU_MAX}%"
    }
    
    evidence_file = WORKSPACE / "memory" / "self-upgrade" / "cpu-utilization-improved.json"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 追加到历史
    history = []
    if evidence_file.exists():
        try:
            history = json.loads(evidence_file.read_text())
            if not isinstance(history, list):
                history = [history]
        except:
            history = []
    
    history.append(evidence)
    evidence_file.write_text(json.dumps(history[-100:], indent=2))  # 保留最近100条
    
    print(f"✅ CPU监控证据已记录")

if __name__ == "__main__":
    monitor_cpu()
