#!/bin/bash
#
# VM状态变更检测与通知系统
# 部署在主节点，监控VM上线/离线状态
#

set -euo pipefail

STATE_DIR="/tmp"
LAST_NOTIFY_FILE="/tmp/vm_last_notify_time"
CHECK_INTERVAL=60

# 获取最新的VM状态文件
get_latest_status_file() {
    ls -t /tmp/vm_status_*.txt 2>/dev/null | head -1
}

# 获取状态文件的修改时间（秒级时间戳）
get_file_mtime() {
    stat -c %Y "$1" 2>/dev/null || echo "0"
}

# 检查是否应该发送通知（避免重复通知）
should_notify() {
    local current_time=$(date +%s)
    local last_notify=0
    
    if [ -f "$LAST_NOTIFY_FILE" ]; then
        last_notify=$(cat "$LAST_NOTIFY_FILE")
    fi
    
    # 如果距离上次通知超过5分钟，允许再次通知
    if [ $((current_time - last_notify)) -gt 300 ]; then
        return 0
    fi
    return 1
}

# 发送通知
send_notification() {
    local status="$1"
    local vm_info="$2"
    
    if [ "$status" = "ONLINE" ]; then
        echo "🌱 **VM已上线！**"
        echo ""
        echo "**双节点系统状态**: 正常"
        echo "**VM信息**: $vm_info"
        echo "**时间**: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "✅ OpenClaw工作节点已就绪，可以接收任务"
    else
        echo "⚠️ **VM已离线！**"
        echo ""
        echo "**双节点系统状态**: 降级（单节点模式）"
        echo "**时间**: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "主节点继续运行，VM恢复后将自动重新连接"
    fi
}

# 主检测逻辑
main() {
    local status_file=$(get_latest_status_file)
    
    if [ -z "$status_file" ]; then
        # 没有状态文件，VM可能离线
        if should_notify; then
            send_notification "OFFLINE" ""
            date +%s > "$LAST_NOTIFY_FILE"
        fi
        exit 0
    fi
    
    local file_mtime=$(get_file_mtime "$status_file")
    local current_time=$(date +%s)
    local time_diff=$((current_time - file_mtime))
    
    # 读取状态文件内容
    local vm_status=$(cat "$status_file" 2>/dev/null || echo "UNKNOWN")
    
    if [ "$time_diff" -lt 120 ]; then
        # 文件在2分钟内更新过，VM在线
        if should_notify; then
            send_notification "ONLINE" "$vm_status"
            date +%s > "$LAST_NOTIFY_FILE"
        fi
    else
        # 文件超过2分钟未更新，VM可能离线
        if should_notify; then
            send_notification "OFFLINE" ""
            date +%s > "$LAST_NOTIFY_FILE"
        fi
    fi
}

main "$@"
