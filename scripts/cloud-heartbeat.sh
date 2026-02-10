#!/bin/bash
#
# 云节点心跳广播系统 v2.0 (Phase 2)
# 部署在云节点，定期向GitHub写入心跳，供本地VM检测
#
# 功能:
# 1. 定期写入心跳到GitHub（带健康状态）
# 2. 故障检测与自恢复
# 3. 优雅降级通知
#

set -euo pipefail

# ============ 配置区域 ============
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${WORKSPACE_DIR:-$SCRIPT_DIR/..}"

# GitHub配置
HEARTBEAT_REPO="${HEARTBEAT_REPO:-useens/linlin-backup}"
HEARTBEAT_BRANCH="${HEARTBEAT_BRANCH:-heartbeat}"
HEARTBEAT_FILE="status/cloud-status.json"
GITHUB_TOKEN_FILE="${GITHUB_TOKEN_FILE:-${HOME}/.config/linlin/github-token}"

# 心跳间隔（秒）
HEARTBEAT_INTERVAL="${HEARTBEAT_INTERVAL:-60}"

# 故障阈值（连续失败几次判定为故障）
FAILURE_THRESHOLD="${FAILURE_THRESHOLD:-3}"

# 日志配置
LOG_FILE="${LOG_FILE:-${WORKSPACE_DIR}/logs/cloud-heartbeat.log}"
PID_FILE="${PID_FILE:-/tmp/cloud-heartbeat.pid}"

# 通知渠道
NOTIFY_TELEGRAM="${NOTIFY_TELEGRAM:-true}"
NOTIFY_FEISHU="${NOTIFY_FEISHU:-true}"

# ============ 颜色输出 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============ 日志函数 ============
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE"
}

log_info() { log "${GREEN}[INFO]${NC} $1"; }
log_warn() { log "${YELLOW}[WARN]${NC} $1"; }
log_error() { log "${RED}[ERROR]${NC} $1"; }
log_debug() { log "${BLUE}[DEBUG]${NC} $1"; }

# ============ 初始化 ============
init() {
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$(dirname "$GITHUB_TOKEN_FILE")"
    
    # 检查GitHub Token
    if [ ! -f "$GITHUB_TOKEN_FILE" ]; then
        log_error "GitHub Token文件不存在: $GITHUB_TOKEN_FILE"
        exit 1
    fi
    
    # 确保心跳分支存在
    ensure_heartbeat_branch
    
    log_info "云节点心跳系统初始化完成"
    log_info "目标仓库: $HEARTBEAT_REPO"
    log_info "心跳间隔: ${HEARTBEAT_INTERVAL}秒"
}

# ============ 获取GitHub Token ============
get_github_token() {
    cat "$GITHUB_TOKEN_FILE" 2>/dev/null || echo ""
}

# ============ 确保心跳分支存在 ============
ensure_heartbeat_branch() {
    local token
    token=$(get_github_token)
    
    if [ -z "$token" ]; then
        log_error "无法获取GitHub Token"
        return 1
    fi
    
    # 检查分支是否存在
    local branch_exists
    branch_exists=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: token $token" \
        "https://api.github.com/repos/${HEARTBEAT_REPO}/git/refs/heads/${HEARTBEAT_BRANCH}")
    
    if [ "$branch_exists" != "200" ]; then
        log_info "创建心跳分支: $HEARTBEAT_BRANCH"
        
        # 获取main分支的SHA
        local main_sha
        main_sha=$(curl -s -H "Authorization: token $token" \
            "https://api.github.com/repos/${HEARTBEAT_REPO}/git/refs/heads/main" | \
            python3 -c "import sys, json; print(json.load(sys.stdin)['object']['sha'])" 2>/dev/null || echo "")
        
        if [ -n "$main_sha" ]; then
            # 创建新分支
            curl -s -X POST \
                -H "Authorization: token $token" \
                -H "Accept: application/vnd.github.v3+json" \
                -d "{\"ref\": \"refs/heads/${HEARTBEAT_BRANCH}\", \"sha\": \"$main_sha\"}" \
                "https://api.github.com/repos/${HEARTBEAT_REPO}/git/refs" > /dev/null
            
            # 初始化状态文件
            init_status_file "$token"
        fi
    fi
}

# ============ 初始化状态文件 ============
init_status_file() {
    local token="$1"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    local content=$(cat <<EOF
{
  "node_type": "cloud",
  "status": "initializing",
  "version": "2.0",
  "initialized_at": "$timestamp",
  "last_heartbeat": null,
  "uptime_seconds": 0,
  "system_info": {
    "hostname": "$(hostname)",
    "platform": "$(uname -s)",
    "architecture": "$(uname -m)"
  },
  "health_checks": {
    "gateway": "unknown",
    "memory_system": "unknown",
    "disk_space": "unknown",
    "network": "unknown"
  },
  "metrics": {
    "memory_usage_percent": 0,
    "disk_usage_percent": 0,
    "cpu_load": 0
  }
}
EOF
)
    
    update_github_file "$token" "$HEARTBEAT_FILE" "$content" "Initialize cloud heartbeat"
}

# ============ 执行健康检查 ============
perform_health_checks() {
    local checks="{}"
    local metrics="{}"
    
    # 检查1: OpenClaw Gateway
    local gateway_status="failed"
    if openclaw gateway status 2>/dev/null | grep -q "running\|active"; then
        gateway_status="healthy"
    elif pgrep -f "openclaw" > /dev/null 2>&1; then
        gateway_status="degraded"
    fi
    
    # 检查2: 内存系统
    local memory_status="failed"
    if [ -d "${WORKSPACE_DIR}/memory" ] && [ -f "${WORKSPACE_DIR}/MEMORY.md" ]; then
        memory_status="healthy"
    fi
    
    # 检查3: 磁盘空间
    local disk_status="healthy"
    local disk_usage
    disk_usage=$(df -h "${WORKSPACE_DIR}" | awk 'NR==2 {print $5}' | tr -d '%')
    if [ "$disk_usage" -gt 90 ]; then
        disk_status="critical"
    elif [ "$disk_usage" -gt 80 ]; then
        disk_status="warning"
    fi
    
    # 检查4: 网络
    local network_status="failed"
    if curl -s --max-time 5 https://api.github.com > /dev/null 2>&1; then
        network_status="healthy"
    fi
    
    # 系统指标
    local memory_usage
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    local cpu_load
    cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    
    # 计算运行时间
    local uptime_seconds=0
    if [ -f "$PID_FILE" ]; then
        local start_time
        start_time=$(stat -c %Y "$PID_FILE" 2>/dev/null || stat -f %m "$PID_FILE" 2>/dev/null || echo "0")
        local current_time
        current_time=$(date +%s)
        uptime_seconds=$((current_time - start_time))
    fi
    
    # 构建JSON
    cat <<EOF
{
  "gateway": "$gateway_status",
  "memory_system": "$memory_status",
  "disk_space": "$disk_status",
  "network": "$network_status"
}
EOF
}

get_metrics() {
    local memory_usage
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    local disk_usage
    disk_usage=$(df "${WORKSPACE_DIR}" | awk 'NR==2 {print $5}' | tr -d '%')
    local cpu_load
    cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    
    cat <<EOF
{
  "memory_usage_percent": ${memory_usage:-0},
  "disk_usage_percent": ${disk_usage:-0},
  "cpu_load": ${cpu_load:-0}
}
EOF
}

# ============ 计算总体状态 ============
calculate_overall_status() {
    local checks="$1"
    
    # 解析健康检查结果
    local gateway=$(echo "$checks" | python3 -c "import sys, json; print(json.load(sys.stdin).get('gateway', 'failed'))")
    local memory=$(echo "$checks" | python3 -c "import sys, json; print(json.load(sys.stdin).get('memory_system', 'failed'))")
    local disk=$(echo "$checks" | python3 -c "import sys, json; print(json.load(sys.stdin).get('disk_space', 'failed'))")
    local network=$(echo "$checks" | python3 -c "import sys, json; print(json.load(sys.stdin).get('network', 'failed'))")
    
    # 计算总体状态
    local failed_count=0
    local warning_count=0
    
    for check in "$gateway" "$memory" "$disk" "$network"; do
        case "$check" in
            failed) ((failed_count++)) ;;
            degraded|warning|critical) ((warning_count++)) ;;
        esac
    done
    
    if [ $failed_count -ge 2 ]; then
        echo "critical"
    elif [ $failed_count -eq 1 ] || [ $warning_count -ge 2 ]; then
        echo "degraded"
    else
        echo "healthy"
    fi
}

# ============ 发送心跳 ============
send_heartbeat() {
    local token
    token=$(get_github_token)
    
    if [ -z "$token" ]; then
        log_error "无法获取GitHub Token"
        return 1
    fi
    
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local local_timestamp
    local_timestamp=$(date +"%Y-%m-%d %H:%M:%S %Z")
    
    # 执行健康检查
    local health_checks
    health_checks=$(perform_health_checks)
    local metrics
    metrics=$(get_metrics)
    local overall_status
    overall_status=$(calculate_overall_status "$health_checks")
    
    # 计算运行时间
    local uptime_seconds=0
    if [ -f "$PID_FILE" ]; then
        local start_time
        start_time=$(stat -c %Y "$PID_FILE" 2>/dev/null || stat -f %m "$PID_FILE" 2>/dev/null || echo "0")
        local current_time
        current_time=$(date +%s)
        uptime_seconds=$((current_time - start_time))
    fi
    
    # 构建心跳数据
    local heartbeat_content=$(cat <<EOF
{
  "node_type": "cloud",
  "status": "$overall_status",
  "version": "2.0",
  "timestamp": "$timestamp",
  "local_time": "$local_timestamp",
  "uptime_seconds": $uptime_seconds,
  "sequence_number": ${SEQUENCE_NUMBER:-0},
  "system_info": {
    "hostname": "$(hostname)",
    "platform": "$(uname -s)",
    "architecture": "$(uname -m)",
    "ip_address": "$(curl -s --max-time 3 ifconfig.me 2>/dev/null || echo 'unknown')"
  },
  "health_checks": $health_checks,
  "metrics": $metrics,
  "capabilities": {
    "auto_recovery": true,
    "local_vm_failover": true,
    "realtime_sync": true
  }
}
EOF
)
    
    log_debug "发送心跳: status=$overall_status"
    
    # 更新GitHub文件
    if update_github_file "$token" "$HEARTBEAT_FILE" "$heartbeat_content" "Heartbeat: $overall_status"; then
        log_info "✅ 心跳发送成功 [$overall_status]"
        
        # 如果状态异常，发送通知
        if [ "$overall_status" != "healthy" ]; then
            send_status_alert "$overall_status" "$health_checks"
        fi
        
        return 0
    else
        log_error "❌ 心跳发送失败"
        return 1
    fi
}

# ============ 更新GitHub文件 ============
update_github_file() {
    local token="$1"
    local file_path="$2"
    local content="$3"
    local message="$4"
    
    # 获取文件当前SHA（如果存在）
    local current_sha
    current_sha=$(curl -s -H "Authorization: token $token" \
        "https://api.github.com/repos/${HEARTBEAT_REPO}/contents/${file_path}?ref=${HEARTBEAT_BRANCH}" | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('sha', ''))" 2>/dev/null || echo "")
    
    # 编码内容
    local encoded_content
    encoded_content=$(echo "$content" | base64 -w 0 2>/dev/null || echo "$content" | base64)
    
    # 构建请求体
    local request_body
    if [ -n "$current_sha" ]; then
        request_body="{\"message\": \"$message\", \"content\": \"$encoded_content\", \"sha\": \"$current_sha\", \"branch\": \"$HEARTBEAT_BRANCH\"}"
    else
        request_body="{\"message\": \"$message\", \"content\": \"$encoded_content\", \"branch\": \"$HEARTBEAT_BRANCH\"}"
    fi
    
    # 发送请求
    local response
    response=$(curl -s -w "\n%{http_code}" -X PUT \
        -H "Authorization: token $token" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Content-Type: application/json" \
        -d "$request_body" \
        "https://api.github.com/repos/${HEARTBEAT_REPO}/contents/${file_path}")
    
    local http_code
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        return 0
    else
        log_error "GitHub API返回: $http_code"
        return 1
    fi
}

# ============ 发送状态告警 ============
send_status_alert() {
    local status="$1"
    local checks="$2"
    
    local message="🚨 云节点状态异常: $status"
    
    case "$status" in
        critical)
            message="🚨 云节点状态: 严重故障！建议立即切换到本地VM"
            ;;
        degraded)
            message="⚠️ 云节点状态: 性能降级，建议关注"
            ;;
    esac
    
    log_warn "$message"
    
    # Telegram通知
    if [ "$NOTIFY_TELEGRAM" = "true" ]; then
        send_telegram_notification "$message"
    fi
    
    # 飞书通知
    if [ "$NOTIFY_FEISHU" = "true" ]; then
        send_feishu_notification "$message"
    fi
}

# ============ Telegram通知 ============
send_telegram_notification() {
    local message="$1"
    
    local bot_token
    bot_token=$(cat "${HOME}/.openclaw/credentials/telegram.token" 2>/dev/null || echo "")
    local chat_id
    chat_id=$(cat "${HOME}/.openclaw/credentials/telegram.chatid" 2>/dev/null || echo "")
    
    if [ -n "$bot_token" ] && [ -n "$chat_id" ]; then
        curl -s -X POST "https://api.telegram.org/bot${bot_token}/sendMessage" \
            -d "chat_id=${chat_id}" \
            -d "text=${message}" \
            -d "parse_mode=HTML" > /dev/null 2>&1 &
    fi
}

# ============ 飞书通知 ============
send_feishu_notification() {
    local message="$1"
    
    # 从凭证文件读取或使用环境变量
    local webhook="${FEISHU_WEBHOOK:-}"
    
    if [ -n "$webhook" ]; then
        curl -s -X POST "$webhook" \
            -H "Content-Type: application/json" \
            -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$message\"}}" > /dev/null 2>&1 &
    fi
}

# ============ 信号处理 ============
cleanup() {
    log_info "接收到停止信号，正在清理..."
    rm -f "$PID_FILE"
    exit 0
}

trap cleanup SIGTERM SIGINT

# ============ 守护模式 ============
run_daemon() {
    log_info "========== 云节点心跳系统启动 =========="
    
    # 写入PID文件
    echo $$ > "$PID_FILE"
    
    # 序列号
    local sequence=0
    local consecutive_failures=0
    
    while true; do
        SEQUENCE_NUMBER=$sequence
        
        if send_heartbeat; then
            consecutive_failures=0
        else
            ((consecutive_failures++))
            log_error "连续失败次数: $consecutive_failures/$FAILURE_THRESHOLD"
            
            if [ $consecutive_failures -ge $FAILURE_THRESHOLD ]; then
                log_error "达到故障阈值，触发自恢复..."
                trigger_self_recovery
            fi
        fi
        
        sequence=$((sequence + 1))
        sleep "$HEARTBEAT_INTERVAL"
    done
}

# ============ 自恢复 ============
trigger_self_recovery() {
    log_warn "执行自恢复流程..."
    
    # 1. 尝试重启Gateway
    log_info "尝试重启OpenClaw Gateway..."
    openclaw gateway restart 2>/dev/null || true
    sleep 5
    
    # 2. 检查关键进程
    if ! pgrep -f "openclaw" > /dev/null 2>&1; then
        log_warn "Gateway未运行，尝试启动..."
        openclaw gateway start 2>/dev/null || true
    fi
    
    # 3. 清理临时文件
    log_info "清理临时文件..."
    find /tmp -name "openclaw*" -type f -mtime +1 -delete 2>/dev/null || true
}

# ============ 单次执行 ============
run_once() {
    init
    send_heartbeat
}

# ============ 状态查询 ============
show_status() {
    local token
    token=$(cat "$GITHUB_TOKEN_FILE" 2>/dev/null || echo "")
    
    if [ -z "$token" ]; then
        echo "❌ 无法获取GitHub Token"
        exit 1
    fi
    
    local status_data
    status_data=$(curl -s -H "Authorization: token $token" \
        "https://api.github.com/repos/${HEARTBEAT_REPO}/contents/${HEARTBEAT_FILE}?ref=${HEARTBEAT_BRANCH}" | \
        python3 -c "import sys, json, base64; data = json.load(sys.stdin); print(base64.b64decode(data['content']).decode())" 2>/dev/null)
    
    if [ -n "$status_data" ]; then
        echo "🌩️  云节点最新状态:"
        echo "$status_data" | python3 -m json.tool 2>/dev/null || echo "$status_data"
    else
        echo "❌ 无法获取状态数据"
        exit 1
    fi
}

# ============ 主流程 ============
main() {
    case "${1:-}" in
        --daemon|-d)
            init
            run_daemon
            ;;
        --status|-s)
            show_status
            ;;
        --test|-t)
            init
            log_info "测试模式: 发送一次心跳"
            send_heartbeat
            ;;
        --setup)
            echo "🌩️  云节点心跳系统 - 配置向导"
            echo ""
            read -rp "GitHub仓库 (格式: 用户名/仓库名) [${HEARTBEAT_REPO}]: " repo
            read -rp "心跳间隔秒数 [${HEARTBEAT_INTERVAL}]: " interval
            read -rp "GitHub Token文件路径 [${GITHUB_TOKEN_FILE}]: " token_file
            
            # 保存配置
            mkdir -p "${HOME}/.config/linlin"
            cat > "${HOME}/.config/linlin/cloud-heartbeat.conf" << EOF
HEARTBEAT_REPO="${repo:-$HEARTBEAT_REPO}"
HEARTBEAT_INTERVAL="${interval:-$HEARTBEAT_INTERVAL}"
GITHUB_TOKEN_FILE="${token_file:-$GITHUB_TOKEN_FILE}"
EOF
            
            echo ""
            echo "✅ 配置已保存到 ${HOME}/.config/linlin/cloud-heartbeat.conf"
            ;;
        --help|-h)
            cat << 'EOF'
云节点心跳广播系统 v2.0

用法: cloud-heartbeat.sh [选项]

选项:
  --daemon, -d    守护模式（持续发送心跳）
  --status, -s    查询当前云节点状态
  --test, -t      测试模式（发送一次心跳）
  --setup         交互式配置向导
  --help, -h      显示帮助

配置文件: ${HOME}/.config/linlin/cloud-heartbeat.conf
日志文件: ${WORKSPACE_DIR}/logs/cloud-heartbeat.log

环境变量:
  HEARTBEAT_REPO      - GitHub仓库名 (默认: useens/linlin-backup)
  HEARTBEAT_INTERVAL  - 心跳间隔秒数 (默认: 60)
  GITHUB_TOKEN_FILE   - Token文件路径

示例:
  # 启动守护模式
  ./cloud-heartbeat.sh --daemon

  # 查询云节点状态
  ./cloud-heartbeat.sh --status

  # 使用systemd管理
  sudo systemctl enable cloud-heartbeat
  sudo systemctl start cloud-heartbeat
EOF
            ;;
        *)
            # 加载配置文件
            if [ -f "${HOME}/.config/linlin/cloud-heartbeat.conf" ]; then
                source "${HOME}/.config/linlin/cloud-heartbeat.conf"
            fi
            run_once
            ;;
    esac
}

main "$@"
