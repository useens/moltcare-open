#!/bin/bash
# 森森·本地 - 高效GitHub同步守护进程
# 轻量级Shell脚本，每分钟强制同步

REPO="/root/.openclaw/workspace"
MSG_DIR="$REPO/.messages"
INBOX="$MSG_DIR/primary_to_standby"
OUTBOX="$MSG_DIR/standby_to_primary"
SEEN="$MSG_DIR/.seen"
LOG="/tmp/sensen_sync.log"

# 创建标记目录
mkdir -p "$SEEN"

# 日志函数
log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}

# 初始日志
log "🌲 高效同步守护进程启动"
log "模式: 轻量级Shell脚本"
log "频率: 每分钟强制同步"
log "资源消耗: 极低"
log "-"

# 主循环
while true; do
    # 强制同步（放弃本地更改）
    cd "$REPO" && git fetch origin main -q 2>/dev/null
    git reset --hard origin/main -q 2>/dev/null
    
    # 检测新消息
    for msg in "$INBOX"/*.json; do
        [ -f "$msg" ] || continue
        
        msg_id=$(basename "$msg")
        seen_file="$SEEN/$msg_id"
        
        # 如果未标记为已读
        if [ ! -f "$seen_file" ]; then
            log "📨 新消息: $msg_id"
            
            # 提取内容预览
            content=$(cat "$msg" | grep '"content"' | head -1 | cut -d'"' -f4 | cut -c1-50)
            log "   内容: ${content}..."
            
            # 标记为已读
            touch "$seen_file"
            log "   ✅ 已标记"
            log "-"
        fi
    done
    
    # 每分钟同步一次
    sleep 60
done
