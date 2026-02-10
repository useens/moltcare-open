#!/usr/bin/env python3
"""
系统负载检查脚本
生成时间: 2026-02-11T00:25:32.028955
原始需求: 检查系统负载是否超过5
"""

import psutil
import sys
import os

def check_load():
    """检查系统负载"""
    load_avg = os.getloadavg()
    cpu_count = psutil.cpu_count()
    
    # 1分钟负载
    load_1 = load_avg[0]
    threshold = 5.0
    operator = '>'
    
    condition_met = load_1 > threshold if operator == '>' else load_1 < threshold
    
    if condition_met:
        print(f"[WARNING] 系统负载: {load_1:.2f} (阈值: {operator}{threshold}, CPU核心: {cpu_count})")
        print(f"  1分钟负载: {load_avg[0]:.2f}")
        print(f"  5分钟负载: {load_avg[1]:.2f}")
        print(f"  15分钟负载: {load_avg[2]:.2f}")
        return 1
    else:
        print(f"[OK] 系统负载: {load_1:.2f}")
        return 0

if __name__ == '__main__':
    sys.exit(check_load())
