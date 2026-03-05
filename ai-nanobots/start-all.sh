#!/bin/bash
# 启动所有10个真小弟 (simple_nanobot)

echo "🚀 启动真小弟集群..."
echo ""

RUNNING=0

for i in {1..10}; do
    port=$((19000+i))
    dir="/root/.openclaw/workspace/ai-nanobots/nanobot-${i}"
    
    echo -n "nanobot-${i} (端口${port})... "
    
    cd "${dir}"
    
    # 使用nanobot.py启动
    nohup python3 nanobot.py > nanobot-${i}.log 2>&1 &
    echo $! > .pid
    
    sleep 1
    
    if ps -p $(cat .pid 2>/dev/null) >/dev/null 2>&1; then
        echo "✅"
        ((RUNNING++))
    else
        echo "❌"
    fi
done

echo ""
echo "========================================"
echo "真小弟启动: ${RUNNING}/10"
echo "========================================"
