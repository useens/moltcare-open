#!/bin/bash
# =============================================================================
# VM端同步接收器部署脚本
# 用法: ./deploy-vm-receiver.sh
# =============================================================================

set -e

VM_HOST="localhost"
VM_PORT="4444"
VM_USER="linlin"
VM_SYNC_DIR="/opt/linlin"
RECEIVER_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/sync-receiver.sh"

echo "========== VM同步接收器部署 =========="
echo "目标: $VM_USER@$VM_HOST:$VM_PORT"
echo ""

# 检查SSH连接
echo "1. 检查SSH连接..."
if ! ssh -p $VM_PORT -o ConnectTimeout=5 "$VM_USER@$VM_HOST" "echo '连接成功'" 2>/dev/null; then
    echo "   ✗ 无法连接到VM"
    echo "   请确保SSH反向隧道已建立:"
    echo "   ssh -R 4444:localhost:22 root@<cloud-server>"
    exit 1
fi
echo "   ✓ SSH连接正常"

# 创建VM端目录
echo ""
echo "2. 创建VM端目录结构..."
ssh -p $VM_PORT "$VM_USER@$VM_HOST" "
    sudo mkdir -p $VM_SYNC_DIR/workspace/{memory,scripts}
    sudo mkdir -p $VM_SYNC_DIR/logs
    sudo mkdir -p $VM_SYNC_DIR/.sync-state
    sudo chown -R $VM_USER:$VM_USER $VM_SYNC_DIR
    echo '目录创建完成'
"
echo "   ✓ 目录结构已创建"

# 复制接收器脚本
echo ""
echo "3. 部署同步接收器..."
scp -P $VM_PORT "$RECEIVER_SCRIPT" "$VM_USER@$VM_HOST:/tmp/sync-receiver.sh"
ssh -p $VM_PORT "$VM_USER@$VM_HOST" "
    sudo mv /tmp/sync-receiver.sh $VM_SYNC_DIR/
    sudo chmod +x $VM_SYNC_DIR/sync-receiver.sh
    sudo chown $VM_USER:$VM_USER $VM_SYNC_DIR/sync-receiver.sh
"
echo "   ✓ 接收器脚本已部署到 $VM_SYNC_DIR/sync-receiver.sh"

# 初始化接收器
echo ""
echo "4. 初始化同步接收器..."
ssh -p $VM_PORT "$VM_USER@$VM_HOST" "$VM_SYNC_DIR/sync-receiver.sh init"
echo "   ✓ 接收器已初始化"

# 测试接收器
echo ""
echo "5. 测试接收器功能..."
if ssh -p $VM_PORT "$VM_USER@$VM_HOST" "$VM_SYNC_DIR/sync-receiver.sh test" 2>&1; then
    echo "   ✓ 接收器测试通过"
else
    echo "   ! 接收器测试发现问题，请检查日志"
fi

# 询问是否安装系统服务
echo ""
echo "6. 系统服务安装（可选）"
read -p "是否安装为systemd服务? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ssh -p $VM_PORT "$VM_USER@$VM_HOST" "$VM_SYNC_DIR/sync-receiver.sh install-service"
    ssh -p $VM_PORT "$VM_USER@$VM_HOST" "sudo systemctl start linlin-sync-receiver"
    echo "   ✓ 系统服务已安装并启动"
fi

echo ""
echo "========== 部署完成 =========="
echo ""
echo "VM端接收器已部署到: $VM_SYNC_DIR/sync-receiver.sh"
echo ""
echo "后续步骤:"
echo "  1. 在主节点测试连接: ./scripts/data-sync.sh test"
echo "  2. 执行首次同步: ./scripts/data-sync.sh sync"
echo "  3. 安装定时同步: 参考 docs/data-sync.md"
echo ""
