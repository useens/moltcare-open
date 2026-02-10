#!/usr/bin/env python3
"""
对话后自动增量记忆入库
在每次对话结束后自动检查并导入新增记忆
"""

import os
import sys
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw/workspace"
SCRIPT_PATH = WORKSPACE / "scripts/incremental-memory-import.py"

def auto_import_after_conversation():
    """
    对话后自动增量导入
    非阻塞方式执行，不影响响应速度
    """
    import subprocess
    
    try:
        # 后台执行增量导入
        subprocess.Popen(
            [sys.executable, str(SCRIPT_PATH)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=WORKSPACE
        )
        return True
    except Exception as e:
        print(f"⚠️ 自动导入启动失败: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    # 立即执行一次
    result = auto_import_after_conversation()
    print(f"自动导入已{'启动' if result else '失败'}")
