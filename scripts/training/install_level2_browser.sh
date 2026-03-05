#!/bin/bash
# 浏览器自动化 安装脚本

echo '🎓 为 NB02 安装工具...'
cd /root/.openclaw/workspace/nanobots/nb02 && python3 -m pip install playwright -q 2>/dev/null
cd /root/.openclaw/workspace/nanobots/nb02 && python3 -m playwright install chromium 2>/dev/null
echo '✅ NB02 安装完成'

echo '🎓 为 NB04 安装工具...'
cd /root/.openclaw/workspace/nanobots/nb04 && python3 -m pip install playwright -q 2>/dev/null
cd /root/.openclaw/workspace/nanobots/nb04 && python3 -m playwright install chromium 2>/dev/null
echo '✅ NB04 安装完成'

echo '🎓 为 NB06 安装工具...'
cd /root/.openclaw/workspace/nanobots/nb06 && python3 -m pip install playwright -q 2>/dev/null
cd /root/.openclaw/workspace/nanobots/nb06 && python3 -m playwright install chromium 2>/dev/null
echo '✅ NB06 安装完成'

echo '🎓 为 NB08 安装工具...'
cd /root/.openclaw/workspace/nanobots/nb08 && python3 -m pip install playwright -q 2>/dev/null
cd /root/.openclaw/workspace/nanobots/nb08 && python3 -m playwright install chromium 2>/dev/null
echo '✅ NB08 安装完成'
