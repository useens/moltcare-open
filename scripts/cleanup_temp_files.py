#!/usr/bin/env python3
"""
临时文件清理脚本
Phase 1: 清理旧临时文件
"""
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

def cleanup_temp_files(temp_dir="/root/.openclaw/workspace/data/vector_memory/realtime", days=7):
    """清理旧临时文件"""
    temp_path = Path(temp_dir)
    if not temp_path.exists():
        print(f"目录不存在: {temp_dir}")
        return
    
    cutoff = time.time() - (days * 24 * 60 * 60)
    count = 0
    total_size = 0
    
    for f in temp_path.glob("*.md"):
        try:
            if f.stat().st_mtime < cutoff:
                size = f.stat().st_size
                f.unlink()
                count += 1
                total_size += size
        except Exception as e:
            print(f"删除失败 {f}: {e}")
    
    print(f"🗑️  清理完成: {count}个文件, {total_size/1024/1024:.2f}MB")
    return count

def setup_auto_cleanup():
    """设置自动清理（添加到cron）"""
    cron_line = "0 2 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/cleanup_temp_files.py \u003e\u003e /root/.openclaw/workspace/logs/cleanup.log 2\u003e\u00261"
    
    # 检查是否已存在
    import subprocess
    result = subprocess.run("crontab -l", shell=True, capture_output=True, text=True)
    if cron_line not in result.stdout:
        # 添加到cron
        new_crontab = result.stdout + cron_line + "\n"
        subprocess.run("echo '{}' | crontab -".format(new_crontab), shell=True)
        print("✅ 自动清理已添加到cron (每天2点)")
    else:
        print("✅ 自动清理已存在")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        setup_auto_cleanup()
    else:
        cleanup_temp_files()
