#!/bin/bash
# 夜间进化容错与自愈系统 v1.0
# 路径: ~/.openclaw/workspace/scripts/night-evolution-guardian.sh

set -e

LOG_FILE="$HOME/.openclaw/workspace/logs/night-evolution-$(date +%Y%m%d).log"
HEALTH_STATE="$HOME/.openclaw/workspace/memory/.night-health-state.json"
ALERT_THRESHOLD=3  # 连续失败3次才报警

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 健康检查
check_health() {
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    local mem_available=$(free -m | awk 'NR==2 {print $7}')
    
    if [ "$disk_usage" -gt 90 ]; then
        log "⚠️ 磁盘空间不足: ${disk_usage}%"
        return 1
    fi
    
    if [ "$mem_available" -lt 500 ]; then
        log "⚠️ 内存不足: ${mem_available}MB 可用"
        return 1
    fi
    
    log "✅ 健康检查通过 (磁盘: ${disk_usage}%, 内存: ${mem_available}MB 可用)"
    return 0
}

# 记录状态
record_state() {
    local stage=$1
    local status=$2
    local message=$3
    
    cat > "$HEALTH_STATE" << EOF
{
  "lastUpdate": "$(date -Iseconds)",
  "stage": "$stage",
  "status": "$status",
  "message": "$message",
  "failCount": $(jq -r '.failCount // 0' "$HEALTH_STATE" 2>/dev/null || echo 0)
}
EOF
}

# 失败处理
handle_failure() {
    local stage=$1
    local fail_count=$(jq -r '.failCount // 0' "$HEALTH_STATE" 2>/dev/null || echo 0)
    fail_count=$((fail_count + 1))
    
    record_state "$stage" "failed" "第${fail_count}次失败"
    
    # 更新失败计数
    jq ".failCount = $fail_count" "$HEALTH_STATE" > "${HEALTH_STATE}.tmp" && mv "${HEALTH_STATE}.tmp" "$HEALTH_STATE"
    
    if [ "$fail_count" -ge "$ALERT_THRESHOLD" ]; then
        log "🚨 连续${ALERT_THRESHOLD}次失败，触发报警"
        # 发送通知（通过OpenClaw消息系统）
        echo "夜间进化连续失败${ALERT_THRESHOLD}次，需要人工检查" > "$HOME/.openclaw/workspace/.alert-need-attention"
    fi
    
    # 智能降级
    if [ "$fail_count" -eq 1 ]; then
        log "🔄 首次失败，30秒后重试..."
        sleep 30
        return 2  # 重试信号
    elif [ "$fail_count" -eq 2 ]; then
        log "🔄 二次失败，切换到轻量模式..."
        export NIGHT_MODE="light"
        return 0  # 继续执行轻量模式
    else
        log "🛑 多次失败，暂停夜间进化"
        return 1  # 终止
    fi
}

# 主执行流程
main() {
    log "=== 夜间进化容错守护者启动 ==="
    
    # 阶段检查
    if ! check_health; then
        handle_failure "health-check"
        exit 1
    fi
    
    record_state "started" "running" "夜间进化开始"
    log "✅ 健康检查通过，开始夜间进化"
    
    # 重置失败计数
    jq '.failCount = 0' "$HEALTH_STATE" > "${HEALTH_STATE}.tmp" && mv "${HEALTH_STATE}.tmp" "$HEALTH_STATE"
}

# 异常捕获
trap 'log "❌ 异常中断"; record_state "unknown" "crashed" "脚本异常退出"; exit 1' ERR

main "$@"
