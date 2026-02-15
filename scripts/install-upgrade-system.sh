#!/bin/bash
# 智能水平升级系统安装脚本

set -e

echo "========================================"
echo "智能水平升级系统安装程序"
echo "========================================"

WORKSPACE="/root/.openclaw/workspace"
SERVICE_NAME="sensen-intelligence-upgrade"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
    echo "错误: 请使用root权限运行此脚本"
    exit 1
fi

# 检查工作目录
if [ ! -d "$WORKSPACE" ]; then
    echo "创建工作目录: $WORKSPACE"
    mkdir -p "$WORKSPACE"
fi

# 确保脚本目录存在
mkdir -p "$WORKSPACE/scripts"
mkdir -p "$WORKSPACE/reports"
mkdir -p "$WORKSPACE/config"
mkdir -p "$WORKSPACE/logs"
mkdir -p "$WORKSPACE/data"

echo ""
echo "[1/5] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3未安装"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "Python版本: $PYTHON_VERSION"

echo ""
echo "[2/5] 安装Systemd服务文件..."

# 创建服务文件
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=Sensen Intelligence Upgrade Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/scripts/intelligence-upgrade-daemon.py
Restart=always
RestartSec=10
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "服务文件已创建: $SERVICE_FILE"

echo ""
echo "[3/5] 重载Systemd配置..."
systemctl daemon-reload

echo ""
echo "[4/5] 启用服务..."
systemctl enable "$SERVICE_NAME"

echo ""
echo "[5/5] 启动服务..."
systemctl start "$SERVICE_NAME"

# 等待服务启动
sleep 2

echo ""
echo "========================================"
echo "安装完成!"
echo "========================================"
echo ""
echo "服务状态:"
systemctl status "$SERVICE_NAME" --no-pager -l

echo ""
echo "常用命令:"
echo "  查看状态: systemctl status $SERVICE_NAME"
echo "  停止服务: systemctl stop $SERVICE_NAME"
echo "  重启服务: systemctl restart $SERVICE_NAME"
echo "  查看日志: journalctl -u $SERVICE_NAME -f"
echo ""
echo "文件位置:"
echo "  服务文件: $SERVICE_FILE"
echo "  工作目录: $WORKSPACE"
echo "  日志目录: $WORKSPACE/logs"
echo "  报告目录: $WORKSPACE/reports"
echo ""

# 生成安装报告
REPORT_FILE="$WORKSPACE/reports/installation-$(date +%Y%m%d).md"
cat > "$REPORT_FILE" << EOF
# 智能水平升级系统安装报告

**安装时间**: $(date -Iseconds)
**服务名称**: $SERVICE_NAME
**安装用户**: root

---

## 安装状态

| 项目 | 状态 |
|------|------|
| 工作目录 | 已创建 |
| Systemd服务文件 | 已安装 |
| Systemd重载 | 已完成 |
| 服务启用 | 已启用 |
| 服务启动 | 已启动 |

## 文件清单

### 核心脚本
- \`scripts/intelligence-assessment.py\` - 智能水平评估
- \`scripts/weakness-analyzer.py\` - 弱项分析
- \`scripts/intelligence-upgrader.py\` - 升级执行
- \`scripts/upgrade-verifier.py\` - 升级验证
- \`scripts/intelligence-upgrade-daemon.py\` - 主控守护进程

### 配置文件
- \`config/upgrade-plan.json\` - 升级计划

### 服务文件
- \`/etc/systemd/system/${SERVICE_NAME}.service\`

## 服务配置

- **执行周期**: 每天 02:00
- **重启策略**: always (10秒间隔)
- **运行用户**: root

## 下一步

系统将在下次02:00自动执行首次升级周期，或手动运行:

\`\`\`bash
# 手动触发单次执行
python3 $WORKSPACE/scripts/intelligence-upgrade-daemon.py --manual
\`\`\`

---
*安装程序自动生成*
EOF

echo "安装报告已生成: $REPORT_FILE"
