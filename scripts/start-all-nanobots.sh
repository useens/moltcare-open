#!/bin/bash
echo "启动10个nanobot..."

for i in {1..10}; do
    export HOME=/root/.openclaw/workspace/nanobot-instances/nanobot-${i}
    cd /root/.openclaw/workspace/nanobot-instances/nanobot-${i}
    nohup /root/.openclaw/workspace/nanobot-env/bin/nanobot gateway -p $((18800+i)) > nanobot.log 2>&1 &
    sleep 2
    echo "nanobot-${i} 启动中..."
done

echo ""
echo "等待所有启动..."
sleep 10

echo ""
echo "检查进程："
ps aux | grep nanobot-gateway | grep -v grep | wc -l
echo "个gateway运行中"

echo ""
echo "查看nanobot-1日志："
tail -10 /root/.openclaw/workspace/nanobot-instances/nanobot-1/nanobot.log