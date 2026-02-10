#!/bin/bash
# Self-Diagnosis System v5.0 Startup Script
# 自我诊断系统启动脚本

WORKSPACE="/root/.openclaw/workspace"
LOGS_DIR="$WORKSPACE/logs"
DATA_DIR="$WORKSPACE/data/diagnosis"
SCRIPTS_DIR="$WORKSPACE/scripts"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 确保目录存在
mkdir -p "$LOGS_DIR" "$DATA_DIR"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

# 检查依赖
if ! python3 -c "import psutil" 2>/dev/null; then
    echo -e "${YELLOW}Installing required packages...${NC}"
    pip3 install psutil aiohttp --quiet
fi

# 函数：启动服务
start_service() {
    echo -e "${BLUE}Starting Self-Diagnosis Service v5.0...${NC}"
    
    # 检查是否已在运行
    if pgrep -f "diagnosis_service.py --start" > /dev/null; then
        echo -e "${YELLOW}Service is already running${NC}"
        return 0
    fi
    
    # 启动服务
    nohup python3 "$SCRIPTS_DIR/diagnosis_service.py" --start > "$LOGS_DIR/diagnosis_service.out" 2>&1 &
    
    sleep 2
    
    if pgrep -f "diagnosis_service.py --start" > /dev/null; then
        echo -e "${GREEN}✓ Service started successfully${NC}"
        echo -e "  - Logs: $LOGS_DIR/diagnosis_service.log"
        echo -e "  - Data: $DATA_DIR"
        return 0
    else
        echo -e "${RED}✗ Failed to start service${NC}"
        return 1
    fi
}

# 函数：停止服务
stop_service() {
    echo -e "${BLUE}Stopping Self-Diagnosis Service...${NC}"
    
    pkill -f "diagnosis_service.py --start" 2>/dev/null
    sleep 1
    
    if pgrep -f "diagnosis_service.py --start" > /dev/null; then
        echo -e "${YELLOW}Service is still running, forcing stop...${NC}"
        pkill -9 -f "diagnosis_service.py --start" 2>/dev/null
    fi
    
    echo -e "${GREEN}✓ Service stopped${NC}"
}

# 函数：显示状态
show_status() {
    echo -e "${BLUE}Self-Diagnosis System Status:${NC}"
    
    if pgrep -f "diagnosis_service.py --start" > /dev/null; then
        echo -e "${GREEN}● Service is running${NC}"
    else
        echo -e "${RED}● Service is not running${NC}"
    fi
    
    echo ""
    python3 "$SCRIPTS_DIR/diagnosis_service.py" --status 2>/dev/null || echo "Service not initialized"
}

# 函数：生成报告
generate_report() {
    echo -e "${BLUE}Generating diagnosis report...${NC}"
    python3 "$SCRIPTS_DIR/diagnosis_service.py" --report
}

# 函数：运行快速检查
quick_check() {
    echo -e "${BLUE}Running quick health check...${NC}"
    python3 "$SCRIPTS_DIR/diagnosis_integration.py" --health
}

# 函数：测试质量分析
test_quality() {
    echo -e "${BLUE}Testing quality analysis...${NC}"
    
    # 测试用例
    test_query="请解释Python的GIL是什么？"
    test_response="Python的GIL（Global Interpreter Lock，全局解释器锁）是CPython解释器中的一个机制，它确保同一时间只有一个线程执行Python字节码。这意味着即使在多核CPU上，Python线程也不能真正并行执行。GIL的存在主要是因为CPython的内存管理不是线程安全的。不过，GIL只影响CPU密集型任务，对于I/O密集型任务，多线程仍然有效。"
    
    python3 "$SCRIPTS_DIR/diagnosis_integration.py" --analyze "test-session" "$test_query" "$test_response"
}

# 主逻辑
case "${1:-}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        sleep 1
        start_service
        ;;
    status)
        show_status
        ;;
    report)
        generate_report
        ;;
    check)
        quick_check
        ;;
    test)
        test_quality
        ;;
    logs)
        tail -f "$LOGS_DIR/diagnosis_service.log"
        ;;
    *)
        echo "Self-Diagnosis System v5.0"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|report|check|test|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the diagnosis service"
        echo "  stop     - Stop the diagnosis service"
        echo "  restart  - Restart the diagnosis service"
        echo "  status   - Show system status"
        echo "  report   - Generate diagnosis report"
        echo "  check    - Run quick health check"
        echo "  test     - Test quality analysis"
        echo "  logs     - View service logs"
        ;;
esac
