#!/bin/bash
# 启动所有10个nanobot

echo "🚀 启动nanobot集群..."
echo ""

NANOBOT_BIN="/root/.openclaw/workspace/nanobot-env/bin/nanobot"
RUNNING=0

for i in {2..10}; do
    nb_id="nanobot-${i}"
    port=$((18800+i))
    home_dir="/root/.openclaw/workspace/nanobot-instances/${nb_id}"
    
    echo -n "启动 ${nb_id} (端口 ${port})... "
    
    cd "${home_dir}"
    export HOME="${home_dir}"
    nohup ${NANOBOT_BIN} gateway -p ${port} > debug.log 2>&1 &
    echo $! > .nanobot.pid
    
    sleep 2
    
    # 检查是否存活
    if ps -p $(cat .nanobot.pid 2>/dev/null) >/dev/null 2>&1; then
        echo "✅"
        ((RUNNING++))
    else
        echo "❌"
    fi
done

echo ""
echo "========================================"
echo "新启动: ${RUNNING}/9"
echo "========================================"
