#!/usr/bin/env python3
"""
健康检查脚本 - OpenClaw 检查 Nanobot
返回值: 0=正常, 1=预警, 2=告警
"""

import os
import sys
import subprocess
import psutil

def check_nanobot_process():
    """检查 Nanobot 进程状态"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "nanobot.py"],
            capture_output=True,
            text=True
        )
        if not result.stdout.strip():
            return 0
        # 过滤掉当前检查脚本自身的进程
        pids = [p for p in result.stdout.strip().split("\n") if p.strip()]
        # 进一步过滤：检查是否是实际的服务进程（排除grep和脚本本身）
        real_pids = []
        for pid in pids:
            try:
                with open(f"/proc/{pid}/cmdline", "r") as f:
                    cmdline = f.read()
                    if "nanobot.py" in cmdline and "health-check" not in cmdline:
                        real_pids.append(pid)
            except:
                pass
        return len(real_pids)
    except:
        return 0

def check_nanobot_memory():
    """检查 Nanobot 内存使用"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
            if 'nanobot.py' in ' '.join(proc.info['cmdline'] or []):
                return proc.info['memory_info'].rss / 1024 / 1024  # MB
    except:
        pass
    return 0

def check_session_size():
    """检查 session 文件大小"""
    try:
        import os
        path = "/root/.openclaw/workspace/nanobot/session.json"
        if os.path.exists(path):
            return os.path.getsize(path) / 1024  # KB
    except:
        pass
    return 0

def check_relay_connection():
    """检查 Bot Relay 连接"""
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:19000/status", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except:
        return False

def main():
    print("🔍 OpenClaw -> Nanobot 健康检查")
    print("-" * 40)
    
    issues = []
    warnings = []
    
    # 1. 检查进程
    proc_count = check_nanobot_process()
    print(f"进程数量: {proc_count}")
    if proc_count == 0:
        issues.append("Nanobot 进程未运行")
    elif proc_count > 1:
        warnings.append(f"存在 {proc_count} 个 Nanobot 进程")
    
    # 2. 检查内存
    memory = check_nanobot_memory()
    print(f"内存使用: {memory:.1f} MB")
    if memory > 100:
        warnings.append(f"内存使用较高: {memory:.1f}MB")
    if memory > 200:
        issues.append(f"内存使用过高: {memory:.1f}MB")
    
    # 3. 检查 session 文件
    session_size = check_session_size()
    print(f"Session 文件: {session_size:.1f} KB")
    if session_size > 500:
        warnings.append(f"Session 文件较大: {session_size:.1f}KB")
    if session_size > 1000:
        issues.append(f"Session 文件过大: {session_size:.1f}KB")
    
    # 4. 检查 Relay 连接
    relay_ok = check_relay_connection()
    print(f"Relay 连接: {'✅' if relay_ok else '❌'}")
    if not relay_ok:
        issues.append("无法连接到 Bot Relay")
    
    print("-" * 40)
    
    # 返回结果
    if issues:
        print(f"❌ 告警: {', '.join(issues)}")
        return 2
    elif warnings:
        print(f"⚠️ 预警: {', '.join(warnings)}")
        return 1
    else:
        print("✅ 一切正常")
        return 0

if __name__ == "__main__":
    sys.exit(main())
