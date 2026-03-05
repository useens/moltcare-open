#!/bin/bash
# 启动简化版AI nanobots

echo "======================================================================"
echo "🚀 启动简化版AI nanobots"
echo "======================================================================"

# 停止旧的进程
pkill -f "simple_nanobot" 2>/dev/null
pkill -f "ai-nanobots.*nanobot.py" 2>/dev/null
sleep 2

echo ""
echo "启动10个nanobots..."
cd /root/.openclaw/workspace/ai-nanobots

for i in {1..10}; do
    NB="nanobot-${i}"
    nohup python3 simple_nanobot.py "${NB}" > "${NB}.log" 2>&1 &
    echo "  ✅ ${NB} 启动"
    sleep 0.5
done

echo ""
echo "等待启动..."
sleep 5

echo ""
echo "检查进程:"
COUNT=$(ps aux | grep "simple_nanobot" | grep -v grep | wc -l)
echo "  运行中的nanobots: ${COUNT}/10"

echo ""
echo "查看日志:"
for i in {1..3}; do
    echo ""
    echo "nanobot-${i}:"
    tail -3 "nanobot-${i}.log"
done

echo ""
echo "======================================================================"
echo "✅ 启动完成！"
echo "======================================================================"
