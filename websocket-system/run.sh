#!/bin/bash
# 快速启动脚本 - 用于开发和测试

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install websockets psutil
else
    source venv/bin/activate
fi

# 创建日志目录
mkdir -p logs

function start_server() {
    echo "启动WebSocket服务器..."
    python src/server.py --host 0.0.0.0 --port 8765 > logs/server.log 2>&1 &
    echo $! > .server.pid
    echo "服务器PID: $(cat .server.pid)"
    sleep 2
    echo "服务器日志:"
    tail -n 5 logs/server.log
}

function start_client() {
    echo "启动WebSocket客户端..."
    python src/client.py --url ws://localhost:8765 --node-id local-node-01 > logs/client.log 2>&1 &
    echo $! > .client.pid
    echo "客户端PID: $(cat .client.pid)"
    sleep 2
    echo "客户端日志:"
    tail -n 5 logs/client.log
}

function stop_all() {
    echo "停止所有服务..."
    if [ -f .server.pid ]; then
        kill $(cat .server.pid) 2>/dev/null || true
        rm .server.pid
    fi
    if [ -f .client.pid ]; then
        kill $(cat .client.pid) 2>/dev/null || true
        rm .client.pid
    fi
    echo "已停止"
}

function run_tests() {
    echo "运行测试..."
    python tests/test_websocket.py --url ws://localhost:8765
}

function show_logs() {
    echo "=== 服务器日志 ==="
    tail -f logs/server.log &
    SERVER_TAIL=$!
    echo "=== 客户端日志 ==="
    tail -f logs/client.log &
    CLIENT_TAIL=$!
    wait $SERVER_TAIL $CLIENT_TAIL
}

case "${1:-help}" in
    server)
        start_server
        ;;
    client)
        start_client
        ;;
    start)
        start_server
        start_client
        echo ""
        echo "服务已启动!"
        echo "查看日志: tail -f logs/server.log logs/client.log"
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        start_server
        start_client
        ;;
    test)
        run_tests
        ;;
    logs)
        show_logs
        ;;
    status)
        if [ -f .server.pid ] && kill -0 $(cat .server.pid) 2>/dev/null; then
            echo "服务器运行中 (PID: $(cat .server.pid))"
        else
            echo "服务器未运行"
        fi
        if [ -f .client.pid ] && kill -0 $(cat .client.pid) 2>/dev/null; then
            echo "客户端运行中 (PID: $(cat .client.pid))"
        else
            echo "客户端未运行"
        fi
        ;;
    docker)
        docker-compose up --build
        ;;
    help|*)
        echo "用法: $0 {server|client|start|stop|restart|test|logs|status|docker}"
        echo ""
        echo "命令:"
        echo "  server   - 仅启动服务器"
        echo "  client   - 仅启动客户端"
        echo "  start    - 启动服务器和客户端"
        echo "  stop     - 停止所有服务"
        echo "  restart  - 重启所有服务"
        echo "  test     - 运行测试"
        echo "  logs     - 查看日志"
        echo "  status   - 查看服务状态"
        echo "  docker   - 使用Docker启动"
        ;;
esac
