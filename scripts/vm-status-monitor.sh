#!/bin/bash
#
# VM状态监控与通知系统 v2
# 部署在主节点，监控VM上线/离线并发送通知
#

set -euo pipefail

STATE_DIR="/tmp"
STATE_FILE="/tmp/vm_monitor_state"
LAST_NOTIFY_FILE="/tmp/vm_last_notify"
LOG_FILE="/root/.openclaw/logs/vm-monitor.log"
VM_SSH_PORT=4444
VM_SSH_KEY="/tmp/linlin_cloud_key"

# 日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查VM是否在线
check_vm_online() {
    if ssh -p "$VM_SSH_PORT" \
           -o ConnectTimeout=5 \
           -o StrictHostKeyChecking=no \
           -o PasswordAuthentication=no \
           -i "$VM_SSH_KEY" \
           root@localhost "echo 'pong'" 2>/dev/null | grep -q "pong"; then
        echo "online"
    else
        echo "offline"
    fi
}

# 获取上次状态
get_last_state() {
    if [ -f "$STATE_FILE" ]; then
        cat "$STATE_FILE"
    else
        echo "unknown"
    fi
}

# 保存当前状态
save_state() {
    echo "$1" > "$STATE_FILE"
}

# 记录通知时间
record_notify() {
    echo "$(date +%s)|$1" > "$LAST_NOTIFY_FILE"
}

# 检查是否应该通知（避免频繁通知）
should_notify() {
    local new_state="$1"
    local current_time=$(date +%s)
    
    if [ ! -f "$LAST_NOTIFY_FILE" ]; then
        return 0
    fi
    
    local last_notify=$(cat "$LAST_NOTIFY_FILE" | cut -d'|' -f1)
    local last_state=$(cat "$LAST_NOTIFY_FILE" | cut -d'|' -f2)
    
    # 状态变化时通知，或离线超过5分钟重复通知
    if [ "$new_state" != "$last_state" ]; then
        return 0
    fi
    
    # 如果离线状态持续超过5分钟，再次通知
    if [ "$new_state" = "offline" ] && [ $((current_time - last_notify)) -gt 300 ]; then
        return 0
    fi
    
    return 1
}

# 生成通知消息
generate_notify_message() {
    local state="$1"
    
    if [ "$state" = "online" ]; then
        echo "🌱 **VM已上线！**

**双节点系统状态**: ✅ 正常
**VM主机**: user-virtual-machine
**时间**: $(date '+%Y-%m-%d %H:%M:%S')
**SSH隧道**: 端口4444已建立

✅ OpenClaw工作节点已就绪，可以接收任务"
    else
        echo "⚠️ **VM已离线！**

**双节点系统状态**: 🔴 降级（单节点模式）
**VM主机**: user-virtual-machine
**时间**: $(date '+%Y-%m-%d %H:%M:%S')
**SSH隧道**: 端口4444连接中断

📍 主节点继续运行，任务将在本地执行
🔄 VM恢复后将自动重新连接"
    fi
}

# 主逻辑
main() {
    mkdir -p "$(dirname "$LOG_FILE")"
    
    local current_state=$(check_vm_online)
    local last_state=$(get_last_state)
    
    log "当前状态: $current_state, 上次状态: $last_state"
    
    # 保存当前状态
    save_state "$current_state"
    
    # 检测状态变化并通知
    if [ "$current_state" != "$last_state" ] || should_notify "$current_state"; then
        if [ "$current_state" = "online" ]; then
            log "🟢 VM已上线！"
        else
            log "🔴 VM已离线！"
        fi
        
        # 输出通知消息（将被发送到飞书）
        generate_notify_message "$current_state"
        
        # 记录通知
        record_notify "$current_state"
    fi
}

main "$@"
