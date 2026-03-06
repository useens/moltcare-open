#!/bin/bash
# 启动 nanobot 小弟模式

echo "🚀 启动 nanobot 小弟模式..."
echo "=================================="

# 确保目录存在
mkdir -p ~/.nanobot-bridge

# 启动桥接器 (后台运行)
nohup python3 /root/.openclaw/workspace/nanobot-bridge/nanobot_sidekick.py > ~/.nanobot-bridge/nanobot.log 2>&1 &

PID=$!
echo $PID > ~/.nanobot-bridge/nanobot.pid

echo "✅ nanobot 小弟已启动"
echo "PID: $PID"
echo "日志: ~/.nanobot-bridge/nanobot.log"
echo ""
echo "使用方式:"
echo "  python3 /root/.openclaw/workspace/nanobot-bridge/sensen_nanobot_bridge.py '你的消息'"
echo ""
echo "停止命令:"
echo "  kill \$(cat ~/.nanobot-bridge/nanobot.pid)"
