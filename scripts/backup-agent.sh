#!/bin/bash
# backup-agent.sh - 定期备份 OpenClaw 工作区

BACKUP_DIR="/root/.openclaw/backups"
WORKSPACE="/root/.openclaw/workspace"
DATE=$(date +%Y%m%d_%H%M%S)

echo "[$(date)] 开始备份..."

# 1. 本地压缩备份
mkdir -p $BACKUP_DIR
BACKUP_FILE="$BACKUP_DIR/workspace_$DATE.tar.gz"

# 进入工作区父目录进行备份
cd $(dirname $WORKSPACE)
tar -czf $BACKUP_FILE \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='*.log' \
  $(basename $WORKSPACE)

echo "[$(date)] 本地备份完成: $BACKUP_FILE"

# 2. 清理旧备份（保留最近 10 个）
ls -t $BACKUP_DIR/workspace_*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null

echo "[$(date)] 备份完成，大小: $(du -h $BACKUP_FILE | cut -f1)"
