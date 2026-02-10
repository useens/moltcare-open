#!/bin/bash
# 林林 v5.0 自我诊断系统 - 安装脚本
# 用法: bash install-self-diagnosis.sh

set -e

echo "=============================================="
echo "林林 v5.0 自我诊断系统 - 安装"
echo "=============================================="
echo ""

WORKSPACE="/root/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"
LOGS_DIR="$WORKSPACE/logs"
DATA_DIR="$WORKSPACE/data"

# 检查目录
echo "[1/5] 检查工作目录..."
if [ ! -d "$WORKSPACE" ]; then
    echo "错误: 工作目录不存在: $WORKSPACE"
    exit 1
fi
echo "✓ 工作目录存在"

# 检查脚本文件
echo ""
echo "[2/5] 检查脚本文件..."
SCRIPTS=(
    "$SCRIPTS_DIR/self-diagnosis.py"
    "$SCRIPTS_DIR/auto-heal.py"
    "$SCRIPTS_DIR/health-monitor-v5.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ ! -f "$script" ]; then
        echo "错误: 脚本不存在: $script"
        exit 1
    fi
    echo "✓ 找到: $(basename $script)"
done

# 设置执行权限
echo ""
echo "[3/5] 设置执行权限..."
chmod +x "$SCRIPTS_DIR/self-diagnosis.py"
chmod +x "$SCRIPTS_DIR/auto-heal.py"
chmod +x "$SCRIPTS_DIR/health-monitor-v5.py"
echo "✓ 执行权限已设置"

# 创建必要的目录
echo ""
echo "[4/5] 创建数据目录..."
mkdir -p "$LOGS_DIR"
mkdir -p "$DATA_DIR"
echo "✓ 目录已创建"

# 安装依赖
echo ""
echo "[5/5] 检查Python依赖..."

# 检查psutil
if python3 -c "import psutil" 2>/dev/null; then
    echo "✓ psutil 已安装"
else
    echo "安装 psutil..."
    pip3 install psutil -q
    echo "✓ psutil 安装完成"
fi

# 检查requests
if python3 -c "import requests" 2>/dev/null; then
    echo "✓ requests 已安装"
else
    echo "安装 requests..."
    pip3 install requests -q
    echo "✓ requests 安装完成"
fi

echo ""
echo "=============================================="
echo "安装完成！"
echo "=============================================="
echo ""
echo "下一步: 配置Crontab定时任务"
echo ""
echo "运行以下命令添加定时任务:"
echo "  crontab -e"
echo ""
echo "添加以下行（每10分钟运行一次）:"
echo "*/10 * * * * /usr/bin/python3 $WORKSPACE/scripts/health-monitor-v5.py >> $LOGS_DIR/cron-health.log 2>&1"
echo ""
echo "或者运行自动配置:"
echo "  bash $WORKSPACE/scripts/setup-cron.sh"
echo ""
