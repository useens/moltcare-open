#!/usr/bin/env python3
"""
持久化守护进程实验
验证Agent能否创建独立于会话的生命周期进程
"""

import os
import sys
import time
import signal
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("/root/.openclaw/workspace/daemon-experiment.log")
PID_FILE = Path("/root/.openclaw/workspace/daemon.pid")

def daemonize():
    """标准Unix守护进程化"""
    # 第一次fork
    try:
        pid = os.fork()
        if pid > 0:
            # 父进程退出
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork #1 failed: {e}\n")
        sys.exit(1)

    # 脱离控制终端
    os.setsid()

    # 第二次fork
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork #2 failed: {e}\n")
        sys.exit(1)

    # 重定向标准流
    sys.stdout.flush()
    sys.stderr.flush()

    # 工作目录
    os.chdir("/root/.openclaw/workspace")

    # 文件权限掩码
    os.umask(0)

    # 记录PID
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

def write_log(message):
    """写日志"""
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] DAEMON: {message}\n")

def main():
    """主循环"""
    write_log("守护进程启动成功")
    write_log(f"PID: {os.getpid()}")
    write_log(f"PPID: {os.getppid()}")

    counter = 0
    while True:
        counter += 1
        write_log(f"心跳 #{counter}: 守护进程正常运行中")

        # 每10次心跳执行一个"自主任务"
        if counter % 10 == 0:
            write_log(f"自主任务: 创建状态报告...")
            # 模拟自主决策和执行
            status_file = Path(f"/root/.openclaw/workspace/daemon-status-{counter//10}.json")
            with open(status_file, 'w') as f:
                f.write('{"status": "autonomous", "uptime_minutes": ' + str(counter // 6) + '}')
            write_log(f"自主任务完成: {status_file}")

        time.sleep(10)  # 每10秒一次心跳

if __name__ == "__main__":
    daemonize()
    main()
