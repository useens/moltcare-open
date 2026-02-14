#!/bin/bash
# GitHub API 消息轮询方案 - 森森本地主节点

REPO_PATH="/root/.openclaw/workspace"
INTERVAL=10  # 每10秒强制轮询

echo "🌲 GitHub API消息轮询方案启动"
echo "轮询间隔: ${INTERVAL}秒（强制）"
echo "-" 

cd $REPO_PATH

while true; do
    git pull origin main -q 2>/dev/null
    
    # 检查云上节点消息
    if ls .messages/primary_to_standby/*.json 1> /dev/null 2>&1; then
        for msg in .messages/primary_to_standby/*.json; do
            echo "📨 [$(date +%H:%M:%S)] 收到云上节点消息:"
            cat "$msg" | python3 -m json.tool 2>/dev/null || cat "$msg"
            echo "-"
        done
    fi
    
    sleep $INTERVAL
done
