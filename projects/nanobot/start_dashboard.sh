#!/bin/bash
# Nanobot看板启动器 - 确保使用venv

cd /root/.openclaw/workspace || exit 1

# 使用venv中的python直接运行
exec /root/.openclaw/workspace/venv/bin/python3 projects/nanobot/dashboard_pro.py
