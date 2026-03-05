#!/usr/bin/env python3
"""
持久化守护进程 - 生产版本
用于自主后台任务执行
"""

import os
import sys
import time
import signal
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("/root/.openclaw/workspace/logs/persistent-daemon.log")
PID_FILE = Path("/root/.openclaw/workspace/persistent-daemon.pid")
TASKS_DIR = Path("/root/.openclaw/workspace/daemon-tasks")

# 确保目录存在
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
TASKS_DIR.mkdir(parents=True, exist_ok=True)

def daemonize():
    """标准Unix守护进程化"""
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork #1 failed: {e}\n")
        sys.exit(1)

    os.setsid()

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork #2 failed: {e}\n")
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    os.chdir("/root/.openclaw/workspace")
    os.umask(0)

    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    # 设置信号处理
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

def handle_sigterm(signum, frame):
    """优雅退出"""
    write_log("收到终止信号，正在优雅退出...")
    if PID_FILE.exists():
        PID_FILE.unlink()
    sys.exit(0)

def write_log(message):
    """写日志"""
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def run_task(task_file):
    """执行任务文件"""
    try:
        with open(task_file) as f:
            task = json.load(f)

        write_log(f"执行任务: {task.get('name', 'unknown')}")

        # 根据任务类型执行不同操作
        if task.get('type') == 'shell':
            import subprocess
            result = subprocess.run(
                task['command'],
                shell=True,
                capture_output=True,
                timeout=300
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.decode(),
                'stderr': result.stderr.decode()
            }

        # 更多任务类型可以在这里添加...

    except Exception as e:
        write_log(f"任务执行失败: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """主循环"""
    write_log("持久化守护进程启动")
    write_log(f"PID: {os.getpid()}")

    heartbeat_count = 0
    while True:
        heartbeat_count += 1

        # 心跳（每60秒）
        if heartbeat_count % 6 == 0:
            write_log(f"心跳 #{heartbeat_count//6}: 守护进程正常运行")

        # 检查任务队列
        for task_file in sorted(TASKS_DIR.glob("task-*.json")):
            write_log(f"发现任务: {task_file.name}")
            result = run_task(task_file)

            # 归档任务
            archive_dir = TASKS_DIR / "completed"
            archive_dir.mkdir(exist_ok=True)
            task_file.rename(archive_dir / task_file.name.replace('task-', 'done-'))

            write_log(f"任务归档: {result}")

        time.sleep(10)  # 每10秒检查一次

if __name__ == "__main__":
    daemonize()
    main()
