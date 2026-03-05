#!/bin/bash
# 基础网络访问 安装脚本

echo '🎓 为 NB01 安装工具...'
cd /root/.openclaw/workspace/nanobots/nb01 && python3 -m pip install requests -q 2>/dev/null
cd /root/.openclaw/workspace/nanobots/nb01 && python3 -m pip install httpx -q 2>/dev/null
echo '✅ NB01 安装完成'

echo '🎓 为 NB02 安装工具...'
cd /root/.openclaw/workspace/nanobots/nb02 && python3 -m pip install requests -q 2>/dev/null
cd /root/.openclaw/workspace/nanobots/nb02 && python3 -m pip install httpx -q 2>/dev/null
echo '✅ NB02 安装完成'

echo '🎓 为 NB03 安装工具...'
cd /root/.openclaw/workspace/nanobots/nb03 && python3 -m pip install requests -q 2>/dev/null
cd /root/.openclaw/workspace/nanobots/nb03 && python3 -m pip install httpx -q 2>/dev/null
echo '✅ NB03 安装完成'

echo '🎓 为 NB04 安装工具...'
cd /root/.openclaw/workspace/nanobots/nb04 && python3 -m pip install requests -q 2>/dev/null
cd /root/.openclaw/workspace/nanobots/nb04 && python3 -m pip install httpx -q 2>/dev/null
echo '✅ NB04 安装完成'

echo '🎓 为 NB05 安装工具...'
cd /root/.openclaw/workspace/nanobots/nb05 && python3 -m pip install requests -q 2>/dev/null
cd /root/.openclaw/workspace/nanobots/nb05 && python3 -m pip install httpx -q 2>/dev/null
echo '✅ NB05 安装完成'
