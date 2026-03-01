#!/bin/bash
# Polymarket 监测系统启动脚本

WORKSPACE="/root/.openclaw/workspace"
SCRIPT_DIR="$WORKSPACE/scripts"
LOG_DIR="$WORKSPACE/logs"
PID_FILE="$WORKSPACE/.polymarket_monitor.pid"

cd "$WORKSPACE"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "监测服务已在运行 (PID: $PID)"
            exit 1
        fi
    fi
    
    echo "启动 Polymarket 监测系统..."
    nohup python3 "$SCRIPT_DIR/polymarket_monitor.py" start > "$LOG_DIR/polymarket_monitor.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "监测服务已启动 (PID: $!)"
    echo "日志: $LOG_DIR/polymarket_monitor.log"
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "停止监测服务 (PID: $PID)..."
            kill "$PID"
            rm "$PID_FILE"
            echo "已停止"
        else
            echo "进程不存在"
            rm "$PID_FILE"
        fi
    else
        echo "监测服务未运行"
    fi
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ 监测服务运行中 (PID: $PID)"
            echo "日志: $LOG_DIR/polymarket_monitor.log"
        else
            echo "❌ 进程不存在"
        fi
    else
        echo "❌ 监测服务未运行"
    fi
}

scan() {
    echo "执行单次扫描..."
    python3 "$SCRIPT_DIR/polymarket_monitor.py" scan
}

stats() {
    python3 "$SCRIPT_DIR/polymarket_monitor.py" stats
}

list() {
    python3 "$SCRIPT_DIR/polymarket_monitor.py" list
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    status)
        status
        ;;
    scan)
        scan
        ;;
    stats)
        stats
        ;;
    list)
        list
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|scan|stats|list}"
        exit 1
        ;;
esac
