#!/usr/bin/env python3
"""
健康检查脚本 - Nanobot 检查 OpenClaw
返回值: 0=正常, 1=预警, 2=告警
"""

import os
import sys
import subprocess
import psutil
import urllib.request
import json

def check_openclaw_gateway():
    """检查 OpenClaw Gateway 状态"""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "openclaw-gateway"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except:
        return "unknown"

def check_openclaw_memory():
    """检查 OpenClaw 内存使用"""
    try:
        total_mem = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'openclaw' in cmdline and 'gateway' in cmdline:
                total_mem += proc.info['memory_info'].rss / 1024 / 1024
        return total_mem
    except:
        return 0

def check_gateway_api():
    """检查 Gateway API 响应"""
    try:
        # 使用 openclaw CLI 检查状态
        result = subprocess.run(
            ["openclaw", "gateway", "status"],
            capture_output=True,
            text=True
        )
        return "running" in result.stdout.lower() or "active" in result.stdout.lower()
    except:
        return False

def check_session_lock():
    """检查 session lock 文件"""
    try:
        import glob
        lock_files = glob.glob("/root/.openclaw/workspace/.claw/sessions/*.lock")
        stale_locks = []
        for lock in lock_files:
            # 检查锁文件是否超过2分钟
            if os.path.getmtime(lock) < time.time() - 120:
                stale_locks.append(lock)
        return len(lock_files), stale_locks
    except:
        return 0, []

def check_log_errors():
    """检查最近日志中的错误"""
    try:
        result = subprocess.run(
            ["journalctl", "--user", "-u", "openclaw-gateway", "--since", "5 minutes ago", "--no-pager"],
            capture_output=True,
            text=True
        )
        errors = [line for line in result.stdout.split("\n") if "error" in line.lower() or "fail" in line.lower()]
        return len(errors)
    except:
        return 0

def main():
    import time
    
    print("🔍 Nanobot -> OpenClaw 健康检查")
    print("-" * 40)
    
    issues = []
    warnings = []
    
    # 1. 检查 Gateway 状态
    gateway_status = check_openclaw_gateway()
    print(f"Gateway 状态: {gateway_status}")
    if gateway_status != "active":
        issues.append(f"Gateway 状态: {gateway_status}")
    
    # 2. 检查内存
    memory = check_openclaw_memory()
    print(f"内存使用: {memory:.1f} MB")
    if memory > 500:
        warnings.append(f"内存警告: {memory:.1f}MB")
    if memory > 800:
        issues.append(f"内存严重: {memory:.1f}MB")
    
    # 3. 检查 API
    api_ok = check_gateway_api()
    print(f"API 响应: {'✅' if api_ok else '❌'}")
    if not api_ok:
        warnings.append("Gateway API 无响应")
    
    # 4. 检查 session lock
    lock_count, stale_locks = check_session_lock()
    print(f"Session locks: {lock_count} (stale: {len(stale_locks)})")
    if stale_locks:
        warnings.append(f"存在 {len(stale_locks)} 个过期锁文件")
    if len(stale_locks) > 3:
        issues.append(f"过多过期锁文件: {len(stale_locks)}")
    
    # 5. 检查日志错误
    error_count = check_log_errors()
    print(f"近期错误: {error_count}")
    if error_count > 5:
        warnings.append(f"近期错误较多: {error_count}")
    
    print("-" * 40)
    
    # 返回结果
    if issues:
        print(f"❌ 告警: {', '.join(issues)}")
        return 2
    elif warnings:
        print(f"⚠️ 预警: {', '.join(warnings)}")
        return 1
    else:
        print("✅ OpenClaw 一切正常")
        return 0

if __name__ == "__main__":
    sys.exit(main())
