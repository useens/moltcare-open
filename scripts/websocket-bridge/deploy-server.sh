#!/bin/bash
# WebSocket Bridge 部署脚本 - 云端节点
# 在云端服务器上执行

set -e

echo "🚀 部署 WebSocket Bridge Server (云端节点)"

# 检查Python和依赖
echo "📦 检查依赖..."
python3 --version || { echo "❌ 需要安装Python3"; exit 1; }

# 安装websockets库
pip3 install websockets psutil || pip install websockets psutil

# 创建日志目录
mkdir -p /root/.openclaw/workspace/logs

# 复制服务文件
cp /root/.openclaw/workspace/scripts/websocket-bridge/sensen-ws-server.service \
   /etc/systemd/system/

# 重载systemd
systemctl daemon-reload

# 启动服务
systemctl enable sensen-ws-server
systemctl restart sensen-ws-server

echo "✅ Server 部署完成！"
echo ""
echo "📊 查看状态: systemctl status sensen-ws-server"
echo "📜 查看日志: tail -f /var/log/sensen-ws-server.log"
echo ""
echo "🔧 配置检查清单:"
echo "  - 防火墙端口 8765 已开放"
echo "  - 公网IP/域名可访问"
echo "  - 如需TLS，配置反向代理(Nginx/Caddy)"