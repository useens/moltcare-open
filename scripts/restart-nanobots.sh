#!/bin/bash
# 重启所有nanobot

echo "=== 重启所有nanobot ==="
pkill -f "simple_nanobot" 2>/dev/null
sleep 2

cd /root/.openclaw/workspace/ai-nanobots

for i in {1..10}; do
    nohup python3 simple_nanobot.py nanobot-${i} > /dev/null 2>&1 &
    echo "  nanobot-${i} 启动"
    sleep 0.5
done

sleep 3

echo ""
echo "✅ 重启完成"
echo ""
echo "检查进程:"
COUNT=$(ps aux | grep "simple_nanobot" | grep -v grep | wc -l)
echo "  ${COUNT}/10 个进程运行中"
