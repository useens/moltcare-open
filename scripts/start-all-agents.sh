#!/bin/bash
# 启动所有Agent

cd /root/.openclaw/workspace/projects/nanobot

# 停止旧进程
pkill -f "agent.py nanobot" 2>/dev/null
sleep 2

# 启动10个Agent
for i in 1 2 3 4 5 6 7 8 9 10; do
    nohup python3 agent.py nanobot-${i} > logs/nanobot-${i}.log 2>&1 &
done

sleep 5

# 检查状态
echo "Agent状态:"
ps aux | grep "agent.py nanobot" | grep -v grep | wc -l
echo "个运行中"
