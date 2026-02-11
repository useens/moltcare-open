#!/bin/bash
#
# VM状态监控 - 状态变化检测版
# 检测状态变化并标记，供外部读取后发送通知
#

set -euo pipefail

STATE_FILE="/tmp/vm_monitor_state"
NOTIFY_FLAG="/tmp/vm_notify_flag"
LOG_FILE="/root/.openclaw/logs/vm-monitor.log"
VM_SSH_PORT=4444
VM_SSH_KEY="/root/.ssh/id_ed25519"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_vm_online() {
    if ssh -p "$VM_SSH_PORT" -o ConnectTimeout=3 -o ConnectionAttempts=1 \
           -o StrictHostKeyChecking=no -o PasswordAuthentication=no \
           -i "$VM_SSH_KEY" root@localhost "echo 'pong'" 2>/dev/null | grep -q "pong"; then
        echo "online"
    else
        echo "offline"
    fi
}

get_last_state() {
    if [ -f "$STATE_FILE" ]; then
        cat "$STATE_FILE"
    else
        echo "unknown"
    fi
}

save_state() {
    echo "$1" > "$STATE_FILE"
}

main() {
    local current_state=$(check_vm_online)
    local last_state=$(get_last_state)
    
    log "当前: $current_state, 上次: $last_state"
    
    # 保存当前状态（无论是否变化）
    save_state "$current_state"
    
    if [ "$current_state" != "$last_state" ]; then
        log "🔔 状态变化: $last_state → $current_state"
        
        local time_str=$(date '+%Y-%m-%d %H:%M:%S')
        
        if [ "$current_state" = "online" ]; then
            log "🟢 VM已上线"
            cat > "$NOTIFY_FLAG" << EOF
STATE=online
TIME=$time_str
FEISHU=🌱 VM已上线！\n\n双节点系统状态: ✅ 正常\nVM主机: user-virtual-machine\n时间: $time_str\nSSH隧道: 端口4444已建立\n\n✅ OpenClaw工作节点已就绪
TELEGRAM=🌱 VM已上线！\n\n双节点系统状态: 正常\nVM主机: user-virtual-machine\n时间: $time_str\nSSH隧道: 端口4444已建立\n\n✅ OpenClaw工作节点已就绪
EOF
        else
            log "🔴 VM已离线"
            cat > "$NOTIFY_FLAG" << EOF
STATE=offline
TIME=$time_str
FEISHU=⚠️ VM已离线！\n\n双节点系统状态: 🔴 降级（单节点模式）\nVM主机: user-virtual-machine\n时间: $time_str\nSSH隧道: 端口4444连接中断\n\n📍 主节点继续运行\n🔄 VM恢复后将自动重新连接
TELEGRAM=⚠️ VM已离线！\n\n双节点系统状态: 降级（单节点模式）\nVM主机: user-virtual-machine\n时间: $time_str\nSSH隧道: 端口4444连接中断\n\n📍 主节点继续运行\n🔄 VM恢复后将自动重新连接
EOF
        fi
        
        # 输出标记供解析
        echo "[STATE_CHANGED:$current_state]"
        cat "$NOTIFY_FLAG"
        log "✅ 通知标记已创建"
    else
        log "状态无变化"
        # 删除旧标记（如果存在）
        rm -f "$NOTIFY_FLAG"
    fi
}

main "$@"
