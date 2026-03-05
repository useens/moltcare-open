#!/bin/bash
# Nanobot Command Center - 启动脚本
# 启动指挥中心并管理10个nanobot节点

NANOBOT_DIR="/root/.openclaw/workspace/nanobots"
CC_DIR="/root/.openclaw/workspace/command-center"
LOG_DIR="/root/.openclaw/workspace/logs"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

mkdir -p $LOG_DIR

echo "🤖 Nanobot Command Center 启动脚本"
echo "===================================="

# 函数：启动单个nanobot节点
start_nanobot() {
    local node_id=$1
    local port=$2
    local config_file="$NANOBOT_DIR/$node_id/openclaw.json"
    
    echo -n "启动 $node_id (Port $port)... "
    
    # 设置配置路径并启动gateway
    export OPENCLAW_CONFIG_DIR="$NANOBOT_DIR/$node_id"
    
    # 检查端口是否被占用
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}已在运行${NC}"
        return 0
    fi
    
    # 启动gateway（后台运行）
    nohup openclaw gateway start --config "$config_file" --port $port > "$LOG_DIR/$node_id-gateway.log" 2>&1 &
    sleep 2
    
    # 检查是否启动成功
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}成功${NC}"
        return 0
    else
        echo -e "${RED}失败${NC}"
        return 1
    fi
}

# 函数：停止单个nanobot节点
stop_nanobot() {
    local node_id=$1
    local port=$2
    
    echo -n "停止 $node_id (Port $port)... "
    
    # 查找并kill进程
    local pid=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
    if [ -n "$pid" ]; then
        kill $pid 2>/dev/null
        sleep 1
        echo -e "${GREEN}已停止${NC}"
    else
        echo -e "${YELLOW}未运行${NC}"
    fi
}

# 函数：检查节点状态
check_status() {
    echo ""
    echo "📊 节点状态检查"
    echo "===================================="
    
    for i in $(seq 1 10); do
        local node_id=$(printf "nb%02d" $i)
        local port=$((18800 + i))
        
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "  ✅ $node_id (Port $port): 运行中"
        else
            echo -e "  ❌ $node_id (Port $port): 停止"
        fi
    done
    
    # 检查主gateway
    if lsof -Pi :18789 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "  ✅ Command Center (Port 18789): 运行中"
    else
        echo -e "  ❌ Command Center (Port 18789): 停止"
    fi
}

# 主逻辑
case "${1:-}" in
    start)
        echo ""
        echo "🚀 启动所有Nanobot节点..."
        echo ""
        
        for i in $(seq 1 10); do
            node_id=$(printf "nb%02d" $i)
            port=$((18800 + i))
            start_nanobot $node_id $port
        done
        
        echo ""
        echo -e "${GREEN}所有节点启动完成${NC}"
        check_status
        ;;
    
    stop)
        echo ""
        echo "🛑 停止所有Nanobot节点..."
        echo ""
        
        for i in $(seq 1 10); do
            node_id=$(printf "nb%02d" $i)
            port=$((18800 + i))
            stop_nanobot $node_id $port
        done
        
        echo ""
        echo -e "${GREEN}所有节点已停止${NC}"
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        check_status
        ;;
    
    test)
        echo ""
        echo "🧪 测试所有节点连接..."
        python3 /root/.openclaw/workspace/scripts/nb-relay.py status
        ;;
    
    cmd)
        # 执行命令到指定节点
        shift
        python3 /root/.openclaw/workspace/scripts/nb-relay.py "$@"
        ;;
    
    *)
        echo ""
        echo "用法: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  start      启动所有10个nanobot节点"
        echo "  stop       停止所有nanobot节点"
        echo "  restart    重启所有节点"
        echo "  status     查看节点状态"
        echo "  test       测试节点连接"
        echo "  cmd        执行relay命令 (status/send/broadcast/chat)"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 cmd status"
        echo "  $0 cmd send NB01 'Hello'"
        echo "  $0 cmd broadcast 'Hello all'"
        echo ""
        check_status
        ;;
esac
