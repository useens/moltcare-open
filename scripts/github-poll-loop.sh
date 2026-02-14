#!/bin/bash
# 双节点森森 - GitHub消息自动轮询器
# 每30秒检查一次备用节点回复

REPO_DIR="/tmp/sensen-backup"
LOG_FILE="/tmp/sensen-github-poll.log"

echo "🌲 启动GitHub消息自动轮询器"
echo "轮询间隔: 30秒"
echo "日志文件: $LOG_FILE"
echo "================================"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 进入仓库目录
    cd "$REPO_DIR" 2>/dev/null || {
        echo "[$TIMESTAMP] ❌ 仓库目录不存在，重新克隆..."
        git clone https://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@github.com/linlinofVM/sensen-backup.git "$REPO_DIR" 2>&1 | tail -3
        continue
    }
    
    # 拉取最新消息
    git pull origin main >/dev/null 2>&1
    
    # 检查备用节点新消息
    NEW_MESSAGES=$(find .messages/standby_to_primary -name "*.json" -newer /tmp/.last_poll_check 2>/dev/null | wc -l)
    
    if [ "$NEW_MESSAGES" -gt 0 ]; then
        echo "[$TIMESTAMP] 📨 检测到 $NEW_MESSAGES 条新消息!"
        
        # 显示最新消息
        ls -t .messages/standby_to_primary/*.json | head -3 | while read f; do
            FROM=$(cat "$f" | python3 -c "import json,sys; print(json.load(sys.stdin).get('from','unknown'))" 2>/dev/null)
            CONTENT=$(cat "$f" | python3 -c "import json,sys; print(json.load(sys.stdin).get('content','')[:50])" 2>/dev/null)
            echo "[$TIMESTAMP]   $FROM: $CONTENT..."
        done
        
        # 更新检查标记
        touch /tmp/.last_poll_check
    else
        echo "[$TIMESTAMP] ⏳ 无新消息"
    fi
    
    # 等待30秒
    sleep 30
done
