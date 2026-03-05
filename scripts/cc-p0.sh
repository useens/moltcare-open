#!/bin/bash
# Command Center P0 - Complete System Launch
# P0完整系统启动脚本

WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs/p0"
PID_DIR="$WORKSPACE/run"

mkdir -p "$LOG_DIR" "$PID_DIR"

# 颜色
c_red='\033[0;31m'
c_green='\033[0;32m'
c_yellow='\033[1;33m'
c_nc='\033[0m' # No Color

log_info() {
    echo -e "${c_green}[INFO]${c_nc} $1"
}

log_warn() {
    echo -e "${c_yellow}[WARN]${c_nc} $1"
}

log_error() {
    echo -e "${c_red}[ERROR]${c_nc} $1"
}

start_nanobots() {
    log_info "启动10个Nanobot节点..."
    $WORKSPACE/scripts/nb-cluster.sh start > "$LOG_DIR/nanobots.log" 2>&1
    sleep 2
    
    # 检查状态
    online=$($WORKSPACE/scripts/nb-cluster.sh status 2>&1 | grep -c "在线")
    if [ "$online" -eq 10 ]; then
        log_info "✅ 10个节点全部在线"
    else
        log_warn "⚠️  只有 $online/10 节点在线"
    fi
}

start_auto_recovery() {
    log_info "启动自动恢复系统..."
    nohup python3 $WORKSPACE/core/auto_recovery.py start > "$LOG_DIR/auto_recovery.log" 2>&1 &
    echo $! > "$PID_DIR/auto_recovery.pid"
    log_info "✅ 自动恢复系统已启动 (PID: $(cat $PID_DIR/auto_recovery.pid))"
}

start_queue_processor() {
    log_info "启动队列处理器..."
    
    # 创建队列处理循环脚本
    cat > "$WORKSPACE/scripts/queue_processor.sh" << 'EOF'
#!/bin/bash
while true; do
    cd /root/.openclaw/workspace
    python3 scripts/nb_relay_v2.py process 5 >> logs/p0/queue_processor.log 2>&1
    sleep 5
done
EOF
    chmod +x "$WORKSPACE/scripts/queue_processor.sh"
    
    nohup "$WORKSPACE/scripts/queue_processor.sh" > /dev/null 2>&1 &
    echo $! > "$PID_DIR/queue_processor.pid"
    log_info "✅ 队列处理器已启动 (PID: $(cat $PID_DIR/queue_processor.pid))"
}

stop_all() {
    log_info "停止所有P0服务..."
    
    # 停止自动恢复
    if [ -f "$PID_DIR/auto_recovery.pid" ]; then
        kill $(cat "$PID_DIR/auto_recovery.pid") 2>/dev/null
        rm -f "$PID_DIR/auto_recovery.pid"
        log_info "✅ 自动恢复系统已停止"
    fi
    
    # 停止队列处理器
    if [ -f "$PID_DIR/queue_processor.pid" ]; then
        kill $(cat "$PID_DIR/queue_processor.pid") 2>/dev/null
        rm -f "$PID_DIR/queue_processor.pid"
        log_info "✅ 队列处理器已停止"
    fi
    
    # 停止nanobots
    $WORKSPACE/scripts/nb-cluster.sh stop > /dev/null 2>&1
    log_info "✅ Nanobot节点已停止"
}

show_status() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           🤖 COMMAND CENTER P0 - 系统状态                   ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 节点状态
    echo "📊 Nanobot 节点:"
    $WORKSPACE/scripts/nb-cluster.sh status 2>&1 | grep -E "NB|汇总"
    
    echo ""
    echo "🔧 P0 服务状态:"
    
    # 自动恢复
    if [ -f "$PID_DIR/auto_recovery.pid" ] && kill -0 $(cat "$PID_DIR/auto_recovery.pid") 2>/dev/null; then
        echo "  ✅ 自动恢复系统: 运行中 (PID: $(cat $PID_DIR/auto_recovery.pid))"
    else
        echo "  ❌ 自动恢复系统: 未运行"
    fi
    
    # 队列处理器
    if [ -f "$PID_DIR/queue_processor.pid" ] && kill -0 $(cat "$PID_DIR/queue_processor.pid") 2>/dev/null; then
        echo "  ✅ 队列处理器: 运行中 (PID: $(cat $PID_DIR/queue_processor.pid))"
    else
        echo "  ❌ 队列处理器: 未运行"
    fi
    
    echo ""
    echo "📁 数据文件:"
    ls -lh $WORKSPACE/data/*.db 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    
    echo ""
}

submit_test_task() {
    log_info "提交测试任务..."
    cd $WORKSPACE
    task_id=$(python3 scripts/nb_relay_v2.py submit "测试P0系统任务" --priority high 2>&1 | grep "任务已提交" | awk '{print $NF}')
    log_info "✅ 测试任务已提交: $task_id"
}

case "${1:-status}" in
    start)
        echo "🚀 启动 Command Center P0 完整系统..."
        echo ""
        start_nanobots
        start_auto_recovery
        start_queue_processor
        echo ""
        log_info "✅ P0系统启动完成！"
        echo ""
        show_status
        ;;
    
    stop)
        stop_all
        ;;
    
    restart)
        stop_all
        sleep 2
        $0 start
        ;;
    
    status)
        show_status
        ;;
    
    test)
        submit_test_task
        ;;
    
    process)
        log_info "手动处理队列..."
        cd $WORKSPACE && python3 scripts/nb_relay_v2.py process ${2:-10}
        ;;
    
    *)
        echo "Command Center P0 System"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|test|process [n]}"
        echo ""
        echo "Commands:"
        echo "  start     启动完整P0系统"
        echo "  stop      停止所有服务"
        echo "  restart   重启系统"
        echo "  status    查看系统状态"
        echo "  test      提交测试任务"
        echo "  process n 手动处理n个任务"
        ;;
esac
