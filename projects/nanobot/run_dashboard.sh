#!/bin/bash
# Nanobot看板启动脚本 - 自动激活venv

cd /root/.openclaw/workspace

# 激活venv
source venv/bin/activate

# 确保rich已安装
pip install rich -q 2>/dev/null

# 运行看板
python3 projects/nanobot/dashboard_pro.py
