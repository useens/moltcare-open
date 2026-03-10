#!/usr/bin/env python3
"""
MoltCare CLI Entry Point
支持直接运行的CLI入口
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cli import main

if __name__ == "__main__":
    sys.exit(main())
