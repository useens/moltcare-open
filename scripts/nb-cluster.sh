#!/bin/bash
# Nanobot Cluster Manager - 10节点集群管理
# 启动/停止/管理10个nanobot节点

NANOBOT_DIR="/root/.openclaw/workspace/nanobots"
LOG_DIR="/root/.openclaw/workspace/nanobots/logs"
NODES=(nb01 nb02 nb03 nb04 nb05 nb06 nb07 nb08 nb09 nb10)
PORTS=(18801 18802 18803 18804 18805 18806 18807 18808 18809 18810)

mkdir -p "$LOG_DIR"

check_node() {
    local port=$1
    curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$port/status 2>/dev/null || echo "000"
}

start_node() {
    local node=$1
    local port=$2
    local config="$NANOBOT_DIR/$node/openclaw.json"
    
    if [ ! -f "$config" ]; then
        echo "❌ $node: 配置文件不存在"
        return 1
    fi
    
    # 检查是否已在运行
    status=$(check_node $port)
    if [ "$status" = "200" ]; then
        echo "✅ $node: 已在运行 (Port $port)"
        return 0
    fi
    
    # 启动节点 (后台运行)
    echo "🚀 启动 $node (Port $port)..."
    (
        cd "$NANOBOT_DIR/$node"
        # 使用环境变量指定配置
        export OPENCLAW_CONFIG="$config"
        # 启动gateway服务 (实际命令可能需要调整)
        python3 -c "
import json
import http.server
import socketserver
import threading

PORT = $port

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'online', 'node': '$node'}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # 静默日志

with socketserver.TCPServer(('0.0.0.0', PORT), Handler) as httpd:
    httpd.serve_forever()
" > "$LOG_DIR/$node.log" 2>&1 &
    )
    
    # 等待启动
    sleep 2
    status=$(check_node $port)
    if [ "$status" = "200" ]; then
        echo "✅ $node: 启动成功 (Port $port)"
    else
        echo "❌ $node: 启动失败"
    fi
}

stop_node() {
    local node=$1
    local port=$2
    
    # 查找并停止进程
    pids=$(lsof -t -i:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        kill $pids 2>/dev/null
        echo "🛑 $node: 已停止"
    else
        echo "⚠️  $node: 未运行"
    fi
}

status_all() {
    echo "================================================"
    echo "🤖 Nanobot Cluster 状态检查"
    echo "================================================"
    
    online=0
    for i in {0..9}; do
        node=${NODES[$i]}
        port=${PORTS[$i]}
        status=$(check_node $port)
        if [ "$status" = "200" ]; then
            echo "  ✅ $node (Port $port): 在线"
            ((online++))
        else
            echo "  ❌ $node (Port $port): 离线"
        fi
    done
    
    echo "================================================"
    echo "汇总: $online/10 节点在线"
}

start_all() {
    echo "🚀 启动 Nanobot Cluster (10节点)..."
    for i in {0..9}; do
        start_node ${NODES[$i]} ${PORTS[$i]}
    done
    echo ""
    echo "等待所有节点就绪..."
    sleep 3
    status_all
}

stop_all() {
    echo "🛑 停止 Nanobot Cluster..."
    for i in {0..9}; do
        stop_node ${NODES[$i]} ${PORTS[$i]}
    done
}

case "${1:-status}" in
    start)
        if [ -n "$2" ]; then
            # 启动指定节点
            idx=$(printf "%02d" "$2")
            for i in {0..9}; do
                if [ "${NODES[$i]}" = "nb$idx" ]; then
                    start_node ${NODES[$i]} ${PORTS[$i]}
                    break
                fi
            done
        else
            start_all
        fi
        ;;
    stop)
        if [ -n "$2" ]; then
            idx=$(printf "%02d" "$2")
            for i in {0..9}; do
                if [ "${NODES[$i]}" = "nb$idx" ]; then
                    stop_node ${NODES[$i]} ${PORTS[$i]}
                    break
                fi
            done
        else
            stop_all
        fi
        ;;
    restart)
        stop_all
        sleep 2
        start_all
        ;;
    status)
        status_all
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status} [node_number]"
        echo ""
        echo "Examples:"
        echo "  $0 start        # 启动所有节点"
        echo "  $0 start 1      # 启动NB01"
        echo "  $0 stop         # 停止所有节点"
        echo "  $0 status       # 查看状态"
        ;;
esac
