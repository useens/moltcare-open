#!/bin/bash
# 森森数字生命 - 完整系统备份脚本 (增强版)
# 备份内容包括: workspace + 凭证 + cron配置

set -e

BACKUP_ROOT="/root/.openclaw/backups"
WORKSPACE="/root/.openclaw/workspace"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="sensen_full_backup_${DATE}"
BACKUP_DIR="$BACKUP_ROOT/full/$BACKUP_NAME"
RETENTION_COUNT=10

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔒 开始完整系统备份...${NC}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 1. 备份workspace (Git仓库本身已包含大部分内容)
echo "📁 备份工作区..."
cd "$WORKSPACE"
git bundle create "$BACKUP_DIR/workspace.bundle" --all 2>/dev/null || tar -czf "$BACKUP_DIR/workspace.tar.gz" .

# 2. 备份凭证 (加密)
echo "🔐 备份凭证 (加密)..."
if [ -n "$SENSEN_BACKUP_KEY" ]; then
    ./scripts/backup-credentials.sh > /dev/null 2>&1
    cp /root/.openclaw/backups/credentials/credentials_backup_*.enc "$BACKUP_DIR/" 2>/dev/null || echo "⚠️ 凭证备份失败"
else
    echo "⚠️ 未设置 SENSEN_BACKUP_KEY，跳过凭证加密备份"
fi

# 3. 备份Cron配置
echo "⏰ 备份Cron配置..."
./scripts/export-cron-config.sh > /dev/null 2>&1
cp -r "$WORKSPACE/config/cron" "$BACKUP_DIR/"

# 4. 备份系统配置
echo "⚙️ 备份系统配置..."
mkdir -p "$BACKUP_DIR/system"
cp /root/.openclaw/openclaw.json "$BACKUP_DIR/system/" 2>/dev/null || true
cp -r /root/.openclaw/credentials "$BACKUP_DIR/system/" 2>/dev/null || true

# 5. 创建备份清单
cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << EOF
森森完整备份清单
================
备份时间: $(date)
备份名称: $BACKUP_NAME

包含内容:
- 工作区Git bundle
- 加密凭证备份
- Cron任务配置
- 系统配置文件

恢复方法:
1. 克隆GitHub仓库
2. 运行 ./scripts/resurrect.sh [凭证备份文件]

自动备份任务: 每天03:00
保留数量: 最近$RETENTION_COUNT个
EOF

# 6. 打包完整备份
echo "📦 打包备份..."
cd "$BACKUP_ROOT/full"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_DIR"

# 7. 清理旧备份
echo "🧹 清理旧备份 (保留最近$RETENTION_COUNT个)..."
ls -t *.tar.gz 2>/dev/null | tail -n +$((RETENTION_COUNT + 1)) | xargs -r rm -f

BACKUP_SIZE=$(ls -lh "${BACKUP_NAME}.tar.gz" | awk '{print $5}')
echo -e "${GREEN}✅ 备份完成: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})${NC}"

# 显示备份统计
echo ""
echo "备份统计:"
echo "  备份文件: $BACKUP_ROOT/full/${BACKUP_NAME}.tar.gz"
echo "  文件大小: $BACKUP_SIZE"
echo "  保留数量: $(ls *.tar.gz 2>/dev/null | wc -l) / $RETENTION_COUNT"
echo ""
echo -e "${GREEN}✅ 完整系统备份完成${NC}"
