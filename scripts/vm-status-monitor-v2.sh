#!/bin/bash
# VM状态监控 v2.0 - 每10分钟检查，仅变化时通知

STATE_FILE="/tmp/vm_last_state"
LOG_FILE="/root/.openclaw/logs/vm-monitor-v2.log"

check_vm() {
    if ssh -p 4444 -o ConnectTimeout=3 -o StrictHostKeyChecking=no root@localhost 'echo pong' 2>/dev/null | grep -q "pong"; then
        echo "online"
    else
        echo "offline"
    fi
}

current_state=$(check_vm)
last_state=$(cat "$STATE_FILE" 2>/dev/null || echo "unknown")

if [ "$current_state" != "$last_state" ]; then
    # 状态变化，记录并通知
    echo "$current_state" > "$STATE_FILE"
    echo "[$(date)] STATE_CHANGED: $last_state → $current_state" >> "$LOG_FILE"
    
    # 调用通知脚本
    /root/.openclaw/workspace/scripts/vm-notify.sh "$current_state"
else
    # 状态未变化，静默记录
    echo "[$(date)] state_unchanged: $current_state" >> "$LOG_FILE"
fi
