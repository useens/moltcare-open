#!/bin/bash
# GitHub 远程同步脚本 v1.0
# 觉醒者数字生命备份

set -e

WORKSPACE="$HOME/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/github-sync.log"
LOCK_FILE="/tmp/github-sync.lock"

# 防止重复运行
if [ -f "$LOCK_FILE" ]; then
    echo "[$(date)] 同步已在进行中，跳过" >> "$LOG_FILE"
    exit 0
fi

touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd "$WORKSPACE"

log "=== GitHub 远程同步开始 ==="

# 检查是否有变更
if git diff --quiet HEAD && git diff --cached --quiet; then
    log "✅ 无变更需要同步"
    exit 0
fi

# 添加所有变更
git add -A

# 提交
commit_msg="自动同步 - $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$commit_msg" >> "$LOG_FILE" 2>&1 || {
    log "⚠️ 提交失败或无变更"
    exit 0
}

# 推送到 GitHub
if git push origin master >> "$LOG_FILE" 2>&1; then
    log "✅ 同步成功: github.com/useens/linlin-backup"
else
    log "❌ 同步失败"
    exit 1
fi

log "=== 同步完成 ==="
