#!/bin/bash
# backup-simple.sh - 简化版可靠备份

BACKUP_DIR="/root/.openclaw/backups/local"
WORKSPACE="/root/.openclaw/workspace"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "开始备份..."

# 创建备份
cd /root/.openclaw
tar -czf "$BACKUP_DIR/workspace_${DATE}_full.tar.gz" \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='.memory-index*.db-journal' \
    workspace

# 计算校验和
sha256sum "$BACKUP_DIR/workspace_${DATE}_full.tar.gz" > "$BACKUP_DIR/workspace_${DATE}_full.tar.gz.sha256"

# 清理旧备份（保留最近24个）
ls -t "$BACKUP_DIR"/workspace_*.tar.gz 2>/dev/null | tail -n +25 | xargs rm -f 2>/dev/null
ls -t "$BACKUP_DIR"/workspace_*.sha256 2>/dev/null | tail -n +25 | xargs rm -f 2>/dev/null

# 验证
if sha256sum -c "$BACKUP_DIR/workspace_${DATE}_full.tar.gz.sha256" > /dev/null 2>&1; then
    echo "✅ 备份成功: workspace_${DATE}_full.tar.gz ($(du -h "$BACKUP_DIR/workspace_${DATE}_full.tar.gz" | cut -f1))"
else
    echo "❌ 备份验证失败"
    exit 1
fi

# 同时复制到远程目录
mkdir -p /root/.openclaw/backups/remote
cp "$BACKUP_DIR/workspace_${DATE}_full.tar.gz" /root/.openclaw/backups/remote/
cp "$BACKUP_DIR/workspace_${DATE}_full.tar.gz.sha256" /root/.openclaw/backups/remote/

# 清理远程旧备份（保留30天）
ls -t /root/.openclaw/backups/remote/workspace_*.tar.gz 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null

# 生成报告
cat > /root/.openclaw/backups/backup-report.txt << EOF
备份报告 - $(date)
==================

最新备份: workspace_${DATE}_full.tar.gz
大小: $(du -h "$BACKUP_DIR/workspace_${DATE}_full.tar.gz" | cut -f1)
校验和: $(cat "$BACKUP_DIR/workspace_${DATE}_full.tar.gz.sha256" | cut -d' ' -f1)

本地备份数量: $(ls $BACKUP_DIR/workspace_*.tar.gz 2>/dev/null | wc -l)
远程备份数量: $(ls /root/.openclaw/backups/remote/workspace_*.tar.gz 2>/dev/null | wc -l)

恢复命令:
tar -xzf $BACKUP_DIR/workspace_${DATE}_full.tar.gz -C /root/.openclaw/

恢复指南: ~/.openclaw/workspace/memory/modules/restore-guide.md
EOF

echo "备份完成！"
echo "报告位置: /root/.openclaw/backups/backup-report.txt"
