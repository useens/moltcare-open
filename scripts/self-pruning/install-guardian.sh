#!/bin/bash
# =============================================================================
# 森森系统精简守护进程安装脚本
# Sensen Pruning Guardian Installation
# =============================================================================

set -e

WORKSPACE="/root/.openclaw/workspace"
SERVICE_DIR="/etc/systemd/system"
echo "=========================================="
echo "🤖 森森系统精简守护进程安装"
echo "=========================================="
echo ""

# 检查目录结构
echo "[1/6] 检查目录结构..."
mkdir -p $WORKSPACE/scripts/self-pruning/{scanner,executor,reports}
mkdir -p $WORKSPACE/memory/self-pruning/reports
mkdir -p $WORKSPACE/logs
mkdir -p $WORKSPACE/config/systemd
echo "  ✓ 目录结构检查完成"

# 检查必要文件
echo "[2/6] 检查必要文件..."
REQUIRED_FILES=(
    "scripts/self-pruning/pruning-guardian.py"
    "scripts/self-pruning/scanner/l2-quick-scan.py"
    "scripts/self-pruning/executor/l2-pruning-executor.py"
    "config/pruning-guardian.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$WORKSPACE/$file" ]; then
        echo "  ❌ 缺少文件: $file"
        exit 1
    fi
done
echo "  ✓ 所有必要文件存在"

# 设置执行权限
echo "[3/6] 设置执行权限..."
chmod +x $WORKSPACE/scripts/self-pruning/*.py
chmod +x $WORKSPACE/scripts/self-pruning/scanner/*.py
chmod +x $WORKSPACE/scripts/self-pruning/executor/*.py
echo "  ✓ 权限设置完成"

# 安装systemd服务
echo "[4/6] 安装systemd服务..."
cp $WORKSPACE/config/systemd/sensen-pruning.service $SERVICE_DIR/
cp $WORKSPACE/config/systemd/sensen-pruning-l3.timer $SERVICE_DIR/
systemctl daemon-reload
echo "  ✓ Systemd服务安装完成"

# 启用服务
echo "[5/6] 启用服务..."
systemctl enable sensen-pruning.service
systemctl enable sensen-pruning-l3.timer
echo "  ✓ 服务已启用"

# 测试运行
echo "[6/6] 测试运行..."
cd $WORKSPACE
python3 scripts/self-pruning/pruning-guardian.py --l2-only
echo "  ✓ 测试运行完成"

echo ""
echo "=========================================="
echo "✅ 安装完成!"
echo "=========================================="
echo ""
echo "启动守护进程:"
echo "  systemctl start sensen-pruning.service"
echo ""
echo "查看状态:"
echo "  systemctl status sensen-pruning.service"
echo "  systemctl list-timers sensen-pruning*"
echo ""
echo "手动执行L2扫描:"
echo "  python3 scripts/self-pruning/pruning-guardian.py --l2-only"
echo ""
echo "手动执行L3评估:"
echo "  python3 scripts/self-pruning/pruning-guardian.py --l3-only"
echo ""
echo "执行精简(试运行):"
echo "  python3 scripts/self-pruning/executor/l2-pruning-executor.py"
echo ""
echo "执行精简(实际):"
echo "  python3 scripts/self-pruning/executor/l2-pruning-executor.py --execute"
echo ""
