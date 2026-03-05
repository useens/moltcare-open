#!/usr/bin/env python3
"""
定时任务状态监控器
检查自动发布任务的执行状态
"""

import subprocess
import time
from pathlib import Path
from datetime import datetime

def check_auto_publish_status():
    """检查自动发布状态"""

    log_file = Path("/root/.openclaw/workspace/data/moltbook/auto-publish.log")

    print("="*60)
    print("🕐 定时任务状态监控")
    print("="*60)
    print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC+8\n")

    # 检查进程
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        output = result.stdout

        sleep_running = "sleep 720" in output
        post_running = "moltbook-wait-and-post.py" in output

        if sleep_running or post_running:
            print("🔄 定时任务状态: 运行中 ✅\n")

            if sleep_running:
                # 获取sleep进程的剩余时间
                try:
                    ps_output = subprocess.check_output(
                        ["ps", "-o", "etime=", "-p", "2175279"],
                        text=True
                    ).strip()
                    print(f"⏳ Sleep进度: {ps_output}")
                    print(f"⏱️  预计发布时间: 约12分钟后\n")
                except:
                    print("⏳ 正在等待冷却时间...\n")
        else:
            print("✅ 定时任务状态: 已完成或未运行\n")

    except Exception as e:
        print(f"⚠️ 无法检查进程状态: {e}\n")

    # 检查日志
    if log_file.exists():
        print("📄 执行日志:\n")
        with open(log_file, "r") as f:
            log_content = f.read()
            if log_content:
                print(log_content)
            else:
                print("  (任务尚未开始执行，日志为空)")
    else:
        print("📄 执行日志: 尚未创建\n")

    # 检查最新活动
    try:
        result = subprocess.run(
            ["/usr/bin/python3", "/root/.openclaw/workspace/scripts/moltbook-activity-tracker.py"],
            capture_output=True,
            text=True
        )
        if result.stdout:
            print("\n📊 最新活动统计:")
            print("="*60)
            # 只打印统计部分
            for line in result.stdout.split('\n'):
                if any(k in line for k in ['帖子', '评论', '点赞', '关注', '剩余']):
                    print(line)
    except:
        pass

    print("\n" + "="*60)

if __name__ == "__main__":
    check_auto_publish_status()
