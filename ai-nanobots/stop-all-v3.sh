#!/bin/bash
# 停止所有 Nanobot V3

echo "🛑 停止 Nanobot V3 集群..."

for bot_id in nanobot-{1..10}; do
    pid_file="/root/.openclaw/workspace/data/neural_hub/${bot_id}.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "  停止 $bot_id (PID: $pid)..."
            kill "$pid"
            rm -f "$pid_file"
        else
            echo "  $bot_id 已不在运行"
            rm -f "$pid_file"
        fi
    fi
done

echo ""
echo "✅ Nanobot V3 集群已停止"
