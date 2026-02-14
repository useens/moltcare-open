#!/bin/bash
# WebSocket Server 部署脚本
# 用于云端节点部署

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/opt/websocket-server"
CONFIG_DIR="/etc/websocket-server"
LOG_DIR="/var/log/websocket-server"
SERVICE_NAME="websocket-server"

echo "=== WebSocket Server 部署脚本 ==="

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 安装依赖
echo "[1/8] 安装系统依赖..."
apt-get update
apt-get install -y python3 python3-venv python3-pip openssl

# 创建用户
echo "[2/8] 创建服务用户..."
if ! id -u websocket &>/dev/null; then
    useradd --system --no-create-home --shell /bin/false websocket
fi

# 创建目录
echo "[3/8] 创建目录结构..."
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR"
chown websocket:websocket "$LOG_DIR"

# 复制文件
echo "[4/8] 复制程序文件..."
cp "$PROJECT_ROOT/src/server.py" "$INSTALL_DIR/"
cp "$PROJECT_ROOT/config/server.json" "$CONFIG_DIR/"

# 创建虚拟环境
echo "[5/8] 创建Python虚拟环境..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install websockets

# 生成SSL证书（如果不存在）
echo "[6/8] 检查SSL证书..."
if [ ! -f "$CONFIG_DIR/server.crt" ]; then
    echo "生成自签名SSL证书..."
    openssl req -x509 -newkey rsa:4096 -keyout "$CONFIG_DIR/server.key" \
        -out "$CONFIG_DIR/server.crt" -days 365 -nodes \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=YourOrg/CN=websocket-server"
    chown websocket:websocket "$CONFIG_DIR/server.key" "$CONFIG_DIR/server.crt"
    chmod 600 "$CONFIG_DIR/server.key"
    echo "SSL证书已生成: $CONFIG_DIR/server.crt"
fi

# 安装systemd服务
echo "[7/8] 安装systemd服务..."
cp "$PROJECT_ROOT/scripts/websocket-server.service" /etc/systemd/system/
systemctl daemon-reload

# 设置权限
echo "[8/8] 设置权限..."
chown -R websocket:websocket "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/server.py"

echo ""
echo "=== 部署完成 ==="
echo ""
echo "启动服务:"
echo "  sudo systemctl enable $SERVICE_NAME"
echo "  sudo systemctl start $SERVICE_NAME"
echo ""
echo "查看状态:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "配置文件: $CONFIG_DIR/server.json"
echo "日志文件: $LOG_DIR/server.log"
