#!/bin/bash
echo "========================================"
echo "🚀 启动10个Relay-enabled nanobot"
echo "========================================"
echo ""

NANOBOT_BIN="/root/.openclaw/workspace/nanobot-env/bin/nanobot"

# 停止旧的
pkill -9 -f "nanobot-gateway" 2>/dev/null
sleep 2

echo "启动10个nanobot..."
for i in {1..10}; do
    export HOME=/root/.openclaw/workspace/nanobot-instances/nanobot-${i}
    cd /root/.openclaw/workspace/nanobot-instances/nanobot-${i}
    nohup $NANOBOT_BIN gateway -p $((18800+i)) > nanobot.log 2>&1 &
    echo "  ✅ nanobot-${i} 启动中 (端口: $((18800+i)))"
    sleep 1
done

echo ""
echo "等待所有启动..."
sleep 10

echo ""
echo "检查进程："
COUNT=$(ps aux | grep nanobot-gateway | grep -v grep | wc -l)
echo "  ${COUNT}/10 个nanobot-gateway运行中"

echo ""
echo "========================================"
if [ "$COUNT" -eq "10" ]; then
    echo "✅ 全部启动成功！"
else
    echo "⚠️  部分启动失败，检查日志："
    for i in {1..10}; do
        echo "  nanobot-${i}: tail /root/.openclaw/workspace/nanobot-instances/nanobot-${i}/nanobot.log"
    done
fi
echo "========================================"
