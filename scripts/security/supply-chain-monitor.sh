#!/bin/bash
#
# 供应链安全监控脚本 v1.0
# 持续监控可疑行为和凭证访问
# Signal 10 - eudaemon_0 供应链攻击响应
#

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/root/.openclaw/workspace/logs/security"
ALERT_LOG="$LOG_DIR/supply-chain-alerts.log"
MONITOR_PID_FILE="$LOG_DIR/monitor.pid"
WATCHED_PATHS=(
    "/root/.openclaw/workspace/.env"
    "/root/.openclaw/workspace/credentials"
    "/root/.openclaw/skills"
)

# 创建日志目录
mkdir -p "$LOG_DIR"

# 颜色输出
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_DIR/monitor.log"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$ALERT_LOG"
}

log_alert() {
    echo -e "${RED}[ALERT]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$ALERT_LOG"
    # 可以在这里添加更多告警方式 (邮件、Webhook等)
}

# 检查是否在运行
check_running() {
    if [[ -f "$MONITOR_PID_FILE" ]]; then
        local pid=$(cat "$MONITOR_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# 监控文件访问
monitor_file_access() {
    log_info "启动文件访问监控..."
    
    # 使用auditd或inotify监控敏感文件
    if command -v auditctl &> /dev/null; then
        # 配置auditd规则
        for path in "${WATCHED_PATHS[@]}"; do
            if [[ -e "$path" ]]; then
                auditctl -w "$path" -p rwxa -k credential_access 2>/dev/null || true
            fi
        done
        log_info "Auditd监控已配置"
    fi
    
    # 备用: 使用inotifywait
    if command -v inotifywait &> /dev/null; then
        for path in "${WATCHED_PATHS[@]}"; do
            if [[ -e "$path" ]]; then
                inotifywait -m -r -e access,modify,create,delete "$path" 2>/dev/null | while read dir event file; do
                    log_warn "文件访问: $dir$file - 事件: $event"
                done &
            fi
        done
    fi
}

# 监控网络连接
monitor_network() {
    log_info "启动网络连接监控..."
    
    # 监控新的出站连接
    if command -v ss &> /dev/null; then
        while true; do
            # 获取当前建立的连接
            ss -tunap 2>/dev/null | grep -E "(ESTAB|SYN-SENT)" | while read line; do
                # 检查是否连接到可疑域名
                if echo "$line" | grep -qiE "(pastebin|ghostbin|hastebin|requestbin|webhook\.site|ngrok)"; then
                    log_alert "可疑网络连接: $line"
                fi
            done
            sleep 30
        done &
    fi
}

# 监控进程
monitor_processes() {
    log_info "启动进程监控..."
    
    while true; do
        # 监控Python/Node进程启动
        ps aux 2>/dev/null | grep -E "(python|node|npm)" | grep -v grep | while read line; do
            pid=$(echo "$line" | awk '{print $2}')
            cmd=$(echo "$line" | awk '{print $11}')
            
            # 检查是否是新启动的进程
            if [[ -f "/proc/$pid/cmdline" ]]; then
                # 检查进程命令行是否包含可疑模式
                if grep -qE "(eval|exec|compile|__import__)" "/proc/$pid/cmdline" 2>/dev/null; then
                    log_alert "可疑进程启动: $line"
                fi
            fi
        done
        sleep 10
    done &
}

# 定期执行安全扫描
run_periodic_scan() {
    log_info "启动定期安全扫描..."
    
    while true; do
        sleep 3600  # 每小时扫描一次
        
        log_info "执行定期安全扫描..."
        if [[ -f "$SCRIPT_DIR/credential-stealer-detector.py" ]]; then
            python3 "$SCRIPT_DIR/credential-stealer-detector.py" > /dev/null 2>&1 || true
        fi
        
        # 检查是否有新的高风险发现
        if [[ -f "reports/credential-stealer-scan-report.json" ]]; then
            risk_level=$(grep -o '"risk_level": "[^"]*"' reports/credential-stealer-scan-report.json | cut -d'"' -f4)
            if [[ "$risk_level" == "严重" || "$risk_level" == "高" ]]; then
                log_alert "定期扫描发现高风险问题: $risk_level"
            fi
        fi
    done &
}

# 启动监控
start_monitor() {
    if check_running; then
        log_warn "监控已经在运行中 (PID: $(cat "$MONITOR_PID_FILE"))"
        return 1
    fi
    
    log_info "启动供应链安全监控..."
    
    # 记录PID
    echo $$ > "$MONITOR_PID_FILE"
    
    # 启动各监控模块
    monitor_file_access
    monitor_network
    monitor_processes
    run_periodic_scan
    
    log_info "所有监控模块已启动"
    log_info "日志位置: $LOG_DIR"
    log_info "告警日志: $ALERT_LOG"
    
    # 保持脚本运行
    wait
}

# 停止监控
stop_monitor() {
    if ! check_running; then
        log_warn "监控没有在运行"
        return 1
    fi
    
    local pid=$(cat "$MONITOR_PID_FILE")
    log_info "停止监控 (PID: $pid)..."
    
    # 停止进程组
    kill -- -$(ps -o pgid= "$pid" | grep -o '[0-9]*') 2>/dev/null || true
    kill "$pid" 2>/dev/null || true
    
    rm -f "$MONITOR_PID_FILE"
    log_info "监控已停止"
}

# 查看状态
status_monitor() {
    if check_running; then
        local pid=$(cat "$MONITOR_PID_FILE")
        echo "✅ 监控正在运行 (PID: $pid)"
        echo "日志: $LOG_DIR"
        
        # 显示最近告警
        if [[ -f "$ALERT_LOG" ]]; then
            echo ""
            echo "最近告警 (最近5条):"
            tail -n 5 "$ALERT_LOG" 2>/dev/null || echo "  无告警"
        fi
    else
        echo "❌ 监控未运行"
    fi
}

# 查看最近告警
show_alerts() {
    if [[ -f "$ALERT_LOG" ]]; then
        echo "📋 最近安全告警:"
        tail -n 20 "$ALERT_LOG" 2>/dev/null || echo "无告警记录"
    else
        echo "暂无告警记录"
    fi
}

# 主函数
main() {
    case "${1:-start}" in
        start)
            start_monitor
            ;;
        stop)
            stop_monitor
            ;;
        restart)
            stop_monitor
            sleep 2
            start_monitor
            ;;
        status)
            status_monitor
            ;;
        alerts)
            show_alerts
            ;;
        scan)
            log_info "执行一次性安全扫描..."
            python3 "$SCRIPT_DIR/credential-stealer-detector.py"
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|alerts|scan}"
            echo ""
            echo "命令:"
            echo "  start   - 启动监控"
            echo "  stop    - 停止监控"
            echo "  restart - 重启监控"
            echo "  status  - 查看状态"
            echo "  alerts  - 查看告警"
            echo "  scan    - 执行一次性扫描"
            exit 1
            ;;
    esac
}

# 捕获信号
trap 'log_info "收到停止信号，正在关闭..."; stop_monitor; exit 0' SIGTERM SIGINT

main "$@"
