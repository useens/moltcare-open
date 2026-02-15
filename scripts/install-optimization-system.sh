#!/bin/bash
# 系统优化系统安装脚本
# Installation script for Sensen System Optimization

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 森森系统优化系统安装程序"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 配置
WORKSPACE="/root/.openclaw/workspace"
SERVICE_NAME="sensen-system-optimization"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo ""
echo "📋 安装配置:"
echo "  工作目录: $WORKSPACE"
echo "  服务名称: $SERVICE_NAME"
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请以root权限运行此脚本"
    exit 1
fi

# 检查工作目录
if [ ! -d "$WORKSPACE" ]; then
    echo "❌ 工作目录不存在: $WORKSPACE"
    exit 1
fi

echo "✅ 权限检查通过"
echo ""

# 检查Python环境
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python版本: $PYTHON_VERSION"
echo ""

# 检查脚本文件
echo "🔍 检查脚本文件..."
SCRIPTS=(
    "scripts/system-evaluation.py"
    "scripts/optimization-opportunity-finder.py"
    "scripts/system-optimizer.py"
    "scripts/optimization-verifier.py"
    "scripts/system-optimization-daemon.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ ! -f "$WORKSPACE/$script" ]; then
        echo "❌ 缺少脚本: $script"
        exit 1
    fi
    chmod +x "$WORKSPACE/$script"
    echo "  ✅ $script"
done
echo ""

# 检查与升级系统的兼容性
echo "🔍 检查与升级系统的兼容性..."
UPGRADE_SERVICE="sensen-intelligence-upgrade.service"
if systemctl list-unit-files | grep -q "$UPGRADE_SERVICE"; then
    echo "✅ 发现升级系统: $UPGRADE_SERVICE"
    echo "  将设置为在升级系统之后启动"
else
    echo "⚠️ 未找到升级系统，将独立运行"
fi
echo ""

# 创建目录结构
echo "📁 创建目录结构..."
mkdir -p "$WORKSPACE/{scripts,reports,config,logs,data,archives}"
echo "✅ 目录结构已创建"
echo ""

# 创建Systemd服务文件
echo "📝 创建Systemd服务文件..."
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=Sensen System Optimization Daemon
After=network.target sensen-intelligence-upgrade.service
Wants=sensen-intelligence-upgrade.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/scripts/system-optimization-daemon.py
Restart=always
RestartSec=10
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 服务文件已创建: $SERVICE_FILE"
echo ""

# 重新加载systemd
echo "🔄 重新加载Systemd配置..."
systemctl daemon-reload
echo "✅ Systemd配置已重载"
echo ""

# 启用服务
echo "🔌 启用服务开机自启..."
systemctl enable "$SERVICE_NAME"
echo "✅ 服务已启用"
echo ""

# 启动服务
echo "▶️ 启动服务..."
if systemctl start "$SERVICE_NAME"; then
    echo "✅ 服务启动成功"
else
    echo "⚠️ 服务启动可能有问题，检查状态..."
fi
echo ""

# 检查状态
echo "📊 服务状态:"
systemctl status "$SERVICE_NAME" --no-pager -l || true
echo ""

# 生成安装报告
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 安装完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 安装摘要:"
echo "  服务名称: $SERVICE_NAME"
echo "  服务文件: $SERVICE_FILE"
echo "  工作目录: $WORKSPACE"
echo ""
echo "🔧 常用命令:"
echo "  查看状态: systemctl status $SERVICE_NAME"
echo "  查看日志: journalctl -u $SERVICE_NAME -f"
echo "  重启服务: systemctl restart $SERVICE_NAME"
echo "  停止服务: systemctl stop $SERVICE_NAME"
echo ""
echo "⚙️ 服务配置:"
echo "  运行模式: 守护进程"
echo "  执行周期: 每天04:00"
echo "  失败重启: 是 (间隔10秒)"
echo "  与升级系统协调: 是"
echo ""
echo "🛡️ 保护项目:"
echo "  • github-backup-sync cron任务"
echo "  • SOUL.md, IDENTITY.md, AGENTS.md, USER.md"
echo "  • 配置凭证 (.env, *.key, *.pem)"
echo "  • 向量记忆系统 (v5.1-v5.5)"
echo "  • Git仓库历史"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
