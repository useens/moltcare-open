#!/bin/bash
# 启动所有10个Nanobot AI Agent

cd /root/.openclaw/workspace
source venv/bin/activate

echo "🚀 启动 10个 Nanobot AI Agent"
echo "=============================="
echo ""

# 创建日志目录
mkdir -p projects/nanobot/logs
mkdir -p projects/nanobot/hub
mkdir -p projects/nanobot/workspaces

# 启动10个Agent
for i in {1..10}; do
    agent_id="nanobot-$i"
    echo "  启动 $agent_id ..."
    
    nohup python3 projects/nanobot/agent.py $agent_id \
        > projects/nanobot/logs/${agent_id}.log 2>&1 &
echo $! > projects/nanobot/logs/${agent_id}.pid
    
    # 错开启动时间
    sleep 3
done

echo ""
echo "✅ 10个 Nanobot AI Agent 已启动"
echo ""
echo "查看状态:"
echo "  日志: tail -f projects/nanobot/logs/nanobot-*.log"
echo "  注册: tail projects/nanobot/hub/registrations.jsonl"
echo "  心跳: tail projects/nanobot/hub/heartbeat.jsonl"
echo ""
echo "停止所有: ./projects/nanobot/stop-all.sh"
