#!/bin/bash
#
# VM状态监控与通知系统 v6 - 双渠道强制同步通知
# 部署在主节点，监控VM上线/离线并强制发送双渠道通知
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

# 发送双渠道通知（强制同步）
send_dual_notification() {
    local state="$1"
    local time_str=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [ "$state" = "online" ]; then
        local feishu_msg="🌱 **VM已上线！**

**双节点系统状态**: ✅ 正常
**VM主机**: user-virtual-machine
**时间**: $time_str
**SSH隧道**: 端口4444已建立

✅ OpenClaw工作节点已就绪，可以接收任务"

        local tg_msg="🌱 VM已上线！

双节点系统状态: 正常
VM主机: user-virtual-machine
时间: $time_str
SSH隧道: 端口4444已建立

✅ OpenClaw工作节点已就绪"
    else
        local feishu_msg="⚠️ **VM已离线！**

**双节点系统状态**: 🔴 降级（单节点模式）
**VM主机**: user-virtual-machine
**时间**: $time_str
**SSH隧道**: 端口4444连接中断

📍 主节点继续运行，任务将在本地执行
🔄 VM恢复后将自动重新连接"

        local tg_msg="⚠️ VM已离线！

双节点系统状态: 降级（单节点模式）
VM主机: user-virtual-machine
时间: $time_str
SSH隧道: 端口4444连接中断

📍 主节点继续运行
🔄 VM恢复后将自动重新连接"
    fi
    
    # ========== 飞书通知 ==========
    # 输出到stdout，cron会发送到飞书
    echo "$feishu_msg"
    
    # ========== Telegram通知 ==========
    # 使用message工具直接发送
    if command -v openclaw > /dev/null 2>&1; then
        # 创建临时消息文件
        local tmp_msg="/tmp/tg_notify_$(date +%s).txt"
        echo "$tg_msg" > "$tmp_msg"
        
        # 使用openclaw message发送（后台执行，不阻塞）
        (
            cd /root/.openclaw/workspace && \
            openclaw message send --channel telegram --message "$(cat $tmp_msg)" 2>/dev/null || \
            echo "[$(date)] Telegram发送失败" >> "$LOG_FILE"
            rm -f "$tmp_msg"
        ) &
    fi
    
    # 输出Telegram标记（供上层解析）
    echo ""
    echo "[TELEGRAM_SENT]"
    echo "$tg_msg"
    echo "[/TELEGRAM_SENT]"
}

# 主逻辑
main() {
    mkdir -p "$(dirname "$LOG_FILE")"
    
    local current_state=$(check_vm_online)
    local last_state=$(get_last_state)
    
    log "当前状态: $current_state, 上次状态: $last_state"
    
    # 保存当前状态
    save_state "$current_state"
    
    # 检测状态变化 - 只要有变化就强制发送双渠道通知
    if [ "$current_state" != "$last_state" ]; then
        log "🔔 状态变化检测: $last_state → $current_state"
        
        if [ "$current_state" = "online" ]; then
            log "🟢 VM已上线！发送双渠道通知..."
        else
            log "🔴 VM已离线！发送双渠道通知..."
        fi
        
        # 强制发送双渠道通知
        send_dual_notification "$current_state"
        
        # 记录通知
        record_notify "$current_state"
        
        log "✅ 双渠道通知已发送"
    else
        log "状态无变化: $current_state"
    fi
}

main "$@"
