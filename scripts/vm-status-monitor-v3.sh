#!/bin/bash
# VM状态监控 v3.0 - 防抖动机制 + 30分钟间隔

STATE_FILE="/tmp/vm_last_state"
PENDING_FILE="/tmp/vm_pending_state"
LOG_FILE="/root/.openclaw/logs/vm-monitor-v3.log"

# 检查VM状态
check_vm() {
    if ssh -p 4444 -o ConnectTimeout=3 -o StrictHostKeyChecking=no root@localhost 'echo pong' 2>/dev/null | grep -q "pong"; then
        echo "online"
    else
        echo "offline"
    fi
}

# 获取当前状态
current_state=$(check_vm)
last_state=$(cat "$STATE_FILE" 2>/dev/null || echo "unknown")

# 如果有待确认的状态，检查是否达到2分钟
if [ -f "$PENDING_FILE" ]; then
    pending_info=$(cat "$PENDING_FILE")
    pending_state=$(echo "$pending_info" | cut -d'|' -f1)
    pending_time=$(echo "$pending_info" | cut -d'|' -f2)
    current_time=$(date +%s)
    elapsed=$((current_time - pending_time))
    
    # 如果当前状态与待确认状态一致且超过2分钟
    if [ "$current_state" = "$pending_state" ] && [ $elapsed -ge 120 ]; then
        # 确认状态变化
        echo "$current_state" > "$STATE_FILE"
        echo "[$(date)] STATE_CONFIRMED: $last_state → $current_state (after ${elapsed}s)" >> "$LOG_FILE"
        
        # 发送通知
        /root/.openclaw/workspace/scripts/vm-notify.sh "$current_state"
        
        # 清除待确认
        rm -f "$PENDING_FILE"
        
        exit 0
    fi
    
    # 如果当前状态与待确认状态不一致，重置待确认
    if [ "$current_state" != "$pending_state" ]; then
        echo "$current_state|$(date +%s)" > "$PENDING_FILE"
        echo "[$(date)] PENDING_RESET: $pending_state → $current_state" >> "$LOG_FILE"
    fi
    
    exit 0
fi

# 检查是否有状态变化
if [ "$current_state" != "$last_state" ]; then
    # 开始防抖动计时
    echo "$current_state|$(date +%s)" > "$PENDING_FILE"
    echo "[$(date)] PENDING_START: $last_state → $current_state (waiting 120s)" >> "$LOG_FILE"
else
    # 状态未变化，静默记录
    echo "[$(date)] state_unchanged: $current_state" >> "$LOG_FILE"
fi
