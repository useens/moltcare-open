#!/bin/bash
# WebSocket Client 部署脚本
# 用于本地节点部署

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/opt/websocket-client"
CONFIG_DIR="/etc/websocket-client"
LOG_DIR="/var/log/websocket-client"
SERVICE_NAME="websocket-client"

echo "=== WebSocket Client 部署脚本 ==="

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 读取服务器配置
read -p "请输入服务器地址 (默认: ws://localhost:8765): " SERVER_URL
SERVER_URL=${SERVER_URL:-ws://localhost:8765}

read -p "请输入节点ID (默认: local-node-01): " NODE_ID
NODE_ID=${NODE_ID:-local-node-01}

read -p "请输入认证Token (默认: demo-token-12345): " TOKEN
TOKEN=${TOKEN:-demo-token-12345}

# 安装依赖
echo "[1/6] 安装系统依赖..."
apt-get update
apt-get install -y python3 python3-venv python3-pip

# 创建用户
echo "[2/6] 创建服务用户..."
if ! id -u websocket &>/dev/null; then
    useradd --system --no-create-home --shell /bin/false websocket
fi

# 创建目录
echo "[3/6] 创建目录结构..."
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR"
chown websocket:websocket "$LOG_DIR"

# 复制文件
echo "[4/6] 复制程序文件..."
cp "$PROJECT_ROOT/src/client.py" "$INSTALL_DIR/"
cp "$PROJECT_ROOT/config/client.json" "$CONFIG_DIR/"

# 更新配置
sed -i "s|ws://localhost:8765|$SERVER_URL|g" "$CONFIG_DIR/client.json"
sed -i "s/local-node-01/$NODE_ID/g" "$CONFIG_DIR/client.json"
sed -i "s/demo-token-12345/$TOKEN/g" "$CONFIG_DIR/client.json"

# 创建虚拟环境
echo "[5/6] 创建Python虚拟环境..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install websockets psutil

# 安装systemd服务
echo "[6/6] 安装systemd服务..."
cp "$PROJECT_ROOT/scripts/websocket-client.service" /etc/systemd/system/

# 更新服务文件中的参数
sed -i "s|ws://your-server:8765|$SERVER_URL|g" /etc/systemd/system/websocket-client.service
sed -i "s/local-node-01/$NODE_ID/g" /etc/systemd/system/websocket-client.service
sed -i "s/demo-token-12345/$TOKEN/g" /etc/systemd/system/websocket-client.service

systemctl daemon-reload

# 设置权限
chown -R websocket:websocket "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/client.py"

echo ""
echo "=== 部署完成 ==="
echo ""
echo "配置信息:"
echo "  服务器: $SERVER_URL"
echo "  节点ID: $NODE_ID"
echo ""
echo "启动服务:"
echo "  sudo systemctl enable $SERVICE_NAME"
echo "  sudo systemctl start $SERVICE_NAME"
echo ""
echo "查看状态:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "配置文件: $CONFIG_DIR/client.json"
echo "日志文件: $LOG_DIR/client.log"
