#!/usr/bin/env python3
"""
端口健康检查脚本
生成时间: 2026-02-11T00:25:32.068715
原始需求: 检查80端口是否在监听
"""

import psutil
import sys
import socket

def check_port(port=None):
    """检查端口监听状态"""
    if not port:
        port = 80
    
    # 检查端口是否在监听
    listening = False
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            listening = True
            break
    
    if listening:
        print(f"[OK] 端口 {port} 正在监听")
        return 0
    else:
        print(f"[WARNING] 端口 {port} 未在监听")
        return 1

if __name__ == '__main__':
    sys.exit(check_port())
