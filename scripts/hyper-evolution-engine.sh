#!/bin/bash
#
# 超进化引擎启动脚本
# 用于启动/停止/重启Hyper Evolution Engine

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_SCRIPT="${SCRIPT_DIR}/hyper-evolution-engine.py"
PID_FILE="/tmp/hyper-evolution-engine.pid"
LOG_FILE="/root/.openclaw/workspace/logs/hyper-evolution-engine.log"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

start_engine() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log_warn "超进化引擎已在运行 (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    log_info "启动超进化引擎..."
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # 启动引擎（后台运行）
    nohup python3 "$ENGINE_SCRIPT" >> "$LOG_FILE" 2>&1 &
    
    # 保存PID
    echo $! > "$PID_FILE"
    
    log_info "超进化引擎已启动 (PID: $(cat "$PID_FILE"))"
    log_info "日志文件: $LOG_FILE"
    
    # 等待确认启动
    sleep 2
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log_info "✅ 引擎运行正常"
    else
        log_error "❌ 引擎启动失败，请检查日志"
        return 1
    fi
}

stop_engine() {
    if [ ! -f "$PID_FILE" ]; then
        log_warn "找不到PID文件，引擎可能未运行"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ! kill -0 "$PID" 2>/dev/null; then
        log_warn "引擎未运行 (PID: $PID)"
        rm -f "$PID_FILE"
        return 1
    fi
    
    log_info "停止超进化引擎 (PID: $PID)..."
    
    # 发送终止信号
    kill -TERM "$PID"
    
    # 等待优雅停止
    for i in {1..10}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            log_info "✅ 引擎已停止"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # 强制停止
    log_warn "强制停止引擎..."
    kill -KILL "$PID" 2>/dev/null || true
    rm -f "$PID_FILE"
    log_info "✅ 引擎已强制停止"
}

restart_engine() {
    log_info "重启超进化引擎..."
    stop_engine || true
    sleep 2
    start_engine
}

status_engine() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_info "✅ 超进化引擎运行中 (PID: $PID)"
            
            # 显示资源使用
            if command -v ps &>/dev/null; then
                CPU=$(ps -p "$PID" -o %cpu= 2>/dev/null || echo "N/A")
                MEM=$(ps -p "$PID" -o %mem= 2>/dev/null || echo "N/A")
                echo "   CPU使用: ${CPU}%"
                echo "   内存使用: ${MEM}%"
            fi
            
            # 显示日志尾部
            if [ -f "$LOG_FILE" ]; then
                echo ""
                echo "最近日志:"
                tail -5 "$LOG_FILE"
            fi
        else
            log_warn "⚠️ 引擎未运行，但PID文件存在"
            rm -f "$PID_FILE"
        fi
    else
        log_warn "❌ 超进化引擎未运行"
    fi
}

# 主命令
case "${1:-status}" in
    start)
        start_engine
        ;;
    stop)
        stop_engine
        ;;
    restart)
        restart_engine
        ;;
    status)
        status_engine
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            log_error "日志文件不存在"
        fi
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
