#!/usr/bin/env python3
"""
网络健康检查脚本
生成时间: 2026-02-11T00:25:32.118121
原始需求: 检查网络连接状态
"""

import psutil
import sys
import socket

def check_network():
    """检查网络状态"""
    stats = psutil.net_io_counters()
    threshold = 80
    operator = '>'
    
    # 获取默认网关连接状态
    try:
        # 测试外部连接
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        network_ok = True
    except:
        network_ok = False
    
    if not network_ok:
        print("[WARNING] 网络连接异常")
        return 1
    
    print(f"[OK] 网络连接正常")
    print(f"  发送: {stats.bytes_sent // 1024} KB")
    print(f"  接收: {stats.bytes_recv // 1024} KB")
    return 0

if __name__ == '__main__':
    sys.exit(check_network())
