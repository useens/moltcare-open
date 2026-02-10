#!/usr/bin/env python3
"""
磁盘健康检查脚本
生成时间: 2026-02-11T00:24:49.142229
原始需求: 检查磁盘空间是否超过85%
"""

import psutil
import sys

def check_disk(path='/'):
    """检查磁盘使用率"""
    disk = psutil.disk_usage(path)
    disk_percent = disk.percent
    threshold = 85.0
    operator = '>'
    
    condition_met = disk_percent > threshold if operator == '>' else disk_percent < threshold
    
    if condition_met:
        print(f"[WARNING] 磁盘使用率: {disk_percent}% (路径: {path})")
        print(f"  总空间: {disk.total // (1024**3)} GB")
        print(f"  已用空间: {disk.used // (1024**3)} GB")
        print(f"  可用空间: {disk.free // (1024**3)} GB")
        return 1
    else:
        print(f"[OK] 磁盘使用率: {disk_percent}% (路径: {path})")
        return 0

if __name__ == '__main__':
    sys.exit(check_disk())
