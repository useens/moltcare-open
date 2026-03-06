#!/bin/bash
# 停止所有Nanobot AI Agent

cd /root/.openclaw/workspace

echo "🛑 停止所有 Nanobot AI Agent"
echo "=============================="
echo ""

for i in {1..10}; do
    agent_id="nanobot-$i"
    pid_file="projects/nanobot/logs/${agent_id}.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "  停止 $agent_id (PID: $pid)..."
            kill "$pid"
        else
            echo "  $agent_id 已停止"
        fi
        rm -f "$pid_file"
    fi
done

echo ""
echo "✅ 所有 Nanobot AI Agent 已停止"
