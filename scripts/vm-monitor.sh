#!/bin/bash
#
# VM在线状态监控器 - 主动检测并通知
# 部署在主节点，检测VM是否上线/离线
#

set -euo pipefail

# 配置
VM_SSH_PORT=4444
VM_SSH_KEY="/tmp/linlin_cloud_key"
CHECK_INTERVAL=30  # 检测间隔（秒）
STATE_FILE="/tmp/vm_last_state"
LOG_FILE="/root/.openclaw/logs/vm-monitor.log"

# 通知配置
FEISHU_WEBHOOK_URL=""  # 如需飞书通知，填写Webhook URL

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

# 发送飞书通知
notify_feishu() {
    local message="$1"
    
    # 通过OpenClaw的message工具发送
    # 由于这个脚本由我执行，我会直接通知用户
    echo "NOTIFY:$message"
}

# 主循环
main() {
    mkdir -p "$(dirname "$LOG_FILE")"
    log "VM监控器启动"
    
    # 初始状态
    local current_state=$(check_vm_online)
    local last_state="${current_state}"
    
    # 如果之前有状态文件，读取它
    if [ -f "$STATE_FILE" ]; then
        last_state=$(cat "$STATE_FILE")
    fi
    
    # 保存当前状态
    echo "$current_state" > "$STATE_FILE"
    
    # 检测状态变化
    if [ "$current_state" = "online" ] && [ "$last_state" = "offline" ]; then
        log "🟢 VM已上线！"
        notify_feishu "🌱 VM已上线！OpenClaw双节点系统就绪"
        
        # 获取VM详细信息
        local vm_info=$(ssh -p "$VM_SSH_PORT" -o StrictHostKeyChecking=no -i "$VM_SSH_KEY" root@localhost "hostname; uptime" 2>/dev/null || echo "Unknown")
        log "VM信息: $vm_info"
        
    elif [ "$current_state" = "offline" ] && [ "$last_state" = "online" ]; then
        log "🔴 VM已离线！"
        notify_feishu "⚠️ VM已离线！双节点系统降级为单节点模式"
    else
        log "VM状态: $current_state (无变化)"
    fi
}

main "$@"
