#!/usr/bin/env python3
"""
内存健康检查脚本
生成时间: 2026-02-11T00:24:49.103689
原始需求: 检查内存使用率是否超过90%
"""

import psutil
import sys

def check_memory():
    """检查内存使用率"""
    mem = psutil.virtual_memory()
    mem_percent = mem.percent
    threshold = 90.0
    operator = '>'
    
    condition_met = mem_percent > threshold if operator == '>' else mem_percent < threshold
    
    if condition_met:
        print(f"[WARNING] 内存使用率: {mem_percent}% (阈值: {operator}{threshold}%)")
        print(f"  总内存: {mem.total // (1024**3)} GB")
        print(f"  可用内存: {mem.available // (1024**3)} GB")
        return 1
    else:
        print(f"[OK] 内存使用率: {mem_percent}%")
        return 0

if __name__ == '__main__':
    sys.exit(check_memory())
