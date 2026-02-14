#!/bin/bash
# 强制定期git pull - 森森本地节点

REPO_PATH="/root/.openclaw/workspace"
INTERVAL=10  # 每10秒强制拉取
LOG_FILE="/tmp/git_pull.log"

echo "🌲 强制定期git pull启动" > $LOG_FILE
echo "间隔: ${INTERVAL}秒" >> $LOG_FILE
echo "开始时间: $(date)" >> $LOG_FILE
echo "-" >> $LOG_FILE

cd $REPO_PATH

while true; do
    echo "[$(date +%H:%M:%S)] 执行git pull..." >> $LOG_FILE
    
    # 强制拉取，放弃本地更改
    git fetch origin main -q
    git reset --hard origin/main -q
    
    # 检查云上节点消息
    if ls .messages/primary_to_standby/*.json 1> /dev/null 2>&1; then
        for msg in .messages/primary_to_standby/*.json; do
            echo "[$(date +%H:%M:%S)] 📨 新消息: $msg" >> $LOG_FILE
            cat "$msg" | python3 -m json.tool 2>/dev/null | head -10 >> $LOG_FILE
            echo "-" >> $LOG_FILE
        done
    fi
    
    sleep $INTERVAL
done
