#!/usr/bin/env python3
"""
CPU健康检查脚本
生成时间: 2026-02-11T00:24:48.061223
原始需求: 检查CPU使用率是否超过80%
"""

import psutil
import sys

def check_cpu():
    """检查CPU使用率"""
    cpu_percent = psutil.cpu_percent(interval=1)
    threshold = 80.0
    operator = '>'
    
    condition_met = cpu_percent > threshold if operator == '>' else cpu_percent < threshold
    
    if condition_met:
        print(f"[WARNING] CPU使用率: {cpu_percent}% (阈值: {operator}{threshold}%)")
        return 1
    else:
        print(f"[OK] CPU使用率: {cpu_percent}%")
        return 0

if __name__ == '__main__':
    sys.exit(check_cpu())
