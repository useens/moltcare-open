#!/bin/bash
# 逐个启动nanobot并验证

echo "🚀 启动nanobot集群..."
echo ""

NANOBOT_BIN="/root/.openclaw/workspace/nanobot-env/bin/nanobot"
RUNNING=0

for i in {1..10}; do
    nb_id="nanobot-${i}"
    port=$((18800+i))
    home_dir="/root/.openclaw/workspace/nanobot-instances/${nb_id}"
    
    echo -n "启动 ${nb_id} (端口 ${port})... "
    
    cd "${home_dir}"
    export HOME="${home_dir}"
    nohup ${NANOBOT_BIN} gateway -p ${port} > nanobot.log 2>&1 &
echo $! > .nanobot.pid
    
    sleep 3
    
    # 检查是否存活
    if ps -p $(cat .nanobot.pid 2>/dev/null) >/dev/null 2>&1; then
        echo "✅ 运行中 (PID: $(cat .nanobot.pid))"
        ((RUNNING++))
    else
        echo "❌ 启动失败"
        tail -3 nanobot.log
    fi
done

echo ""
echo "========================================"
echo "总计: ${RUNNING}/10 运行中"
echo "========================================"
