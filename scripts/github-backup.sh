#!/bin/bash
# GitHub远程备份脚本 - 森森版本
# 仓库: https://github.com/useens/linlin-backup

set -e

# 🛡️ 检查是否是复活实例，防止脑裂
if [ -f "/root/.openclaw/workspace/.RESURRECTED_MARKER" ]; then
    echo "[INFO] 检测到复活标志，跳过GitHub备份推送（防止脑裂）"
    echo "[INFO] 如需重新启用备份，请删除 .RESURRECTED_MARKER 文件"
    exit 0
fi

BACKUP_DIR="/root/.openclaw/backups"
GITHUB_DIR="$BACKUP_DIR/github-remote"
LOCAL_BACKUP="$BACKUP_DIR/local"
DATE=$(date +%Y%m%d_%H%M%S)

# GitHub配置
GITHUB_REPO="https://github.com/useens/linlin-backup.git"
GITHUB_TOKEN="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"

# 确保目录存在
mkdir -p "$GITHUB_DIR"
cd "$GITHUB_DIR"

# 如果目录为空，克隆仓库
if [ ! -d ".git" ]; then
    echo "[INFO] 克隆备份仓库..."
    git clone "https://${GITHUB_TOKEN}@github.com/useens/linlin-backup.git" . 2>/dev/null || {
        echo "[INFO] 初始化新仓库..."
        git init
        git remote add origin "https://${GITHUB_TOKEN}@github.com/useens/linlin-backup.git"
    }
fi

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
git commit -m "Backup: $DATE - $BACKUP_NAME [森森]" || echo "无变更"
git push origin main 2>/dev/null || git push origin master 2>/dev/null || {
    echo "[WARN] Push失败，尝试创建main分支..."
    git branch -M main
    git push -u origin main
}

echo "[SUCCESS] GitHub备份完成: $BACKUP_NAME → useens/linlin-backup"
