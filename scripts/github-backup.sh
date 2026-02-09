#!/bin/bash
# GitHub远程备份脚本

set -e

BACKUP_DIR="/root/.openclaw/backups"
GITHUB_DIR="$BACKUP_DIR/github-remote"
LOCAL_BACKUP="$BACKUP_DIR/local"
DATE=$(date +%Y%m%d_%H%M%S)

# 确保目录存在
mkdir -p "$GITHUB_DIR"
cd "$GITHUB_DIR"

# 获取最新本地备份
LATEST_BACKUP=$(ls -t $LOCAL_BACKUP/workspace_*.tar.gz 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "[ERROR] 无可用本地备份"
    exit 1
fi

# 复制备份到GitHub目录
BACKUP_NAME=$(basename "$LATEST_BACKUP")
cp "$LATEST_BACKUP" .
cp "${LATEST_BACKUP}.sha256" . 2>/dev/null || echo "无校验和文件"

# Git操作
git add .
git commit -m "Backup: $DATE - $BACKUP_NAME" || echo "无变更"
git push origin main || git push origin master

echo "[SUCCESS] GitHub备份完成: $BACKUP_NAME"
