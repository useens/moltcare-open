#!/bin/bash
# WebSocket Bridge 部署脚本 - 本地节点
# 在本地服务器上执行

set -e

echo "🚀 部署 WebSocket Bridge Client (本地节点)"

# 获取云端服务器地址
echo "请输入云端服务器地址 (如: ws://1.2.3.4:8765 或 wss://cloud.example.com):"
read -r SERVER_URI

# 更新客户端配置
sed -i "s|SERVER_URI = \"wss://your-cloud-server:8765\"|SERVER_URI = \"${SERVER_URI}\"|g" \
    /root/.openclaw/workspace/scripts/websocket-bridge/client.py

echo "📦 检查依赖..."
python3 --version || { echo "❌ 需要安装Python3"; exit 1; }
pip3 install websockets psutil || pip install websockets psutil

# 创建日志目录
mkdir -p /root/.openclaw/workspace/logs

# 复制服务文件
cp /root/.openclaw/workspace/scripts/websocket-bridge/sensen-ws-client.service \
   /etc/systemd/system/

# 重载systemd
systemctl daemon-reload

# 启动服务
systemctl enable sensen-ws-client
systemctl restart sensen-ws-client

echo "✅ Client 部署完成！"
echo ""
echo "📊 查看状态: systemctl status sensen-ws-client"
echo "📜 查看日志: tail -f /var/log/sensen-ws-client.log"
echo ""
echo "🔧 配置:"
echo "  - 服务器地址: ${SERVER_URI}"
echo "  - 客户端ID: sensen-local"
echo "  - 认证Token: sensen-bridge-2024"