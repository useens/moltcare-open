#!/bin/bash
# 强制Git同步脚本 - 云端节点静默同步
# 用途：定时强制同步GitHub状态，不检查脑裂标志

set -e

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/forced-git-sync.log"
LOCK_FILE="/tmp/forced-git-sync.lock"

# 防止重复运行
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "[$(date)] 同步已在进行中(PID: $PID)，跳过" >> "$LOG_FILE"
        exit 0
    else
        rm -f "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

cd "$WORKSPACE"

log "=== 强制Git同步开始 ==="

# 检查Git仓库状态
if [ ! -d ".git" ]; then
    log "❌ 不是Git仓库"
    exit 1
fi

# 获取当前分支
BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
log "当前分支: $BRANCH"

# 检查远程仓库配置
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE_URL" ]; then
    log "❌ 未配置远程仓库"
    exit 1
fi
log "远程仓库: $REMOTE_URL"

# 获取GitHub Token
GITHUB_TOKEN=$(grep GITHUB_TOKEN .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "")
if [ -z "$GITHUB_TOKEN" ]; then
    log "⚠️ 未找到GITHUB_TOKEN，尝试使用现有凭据"
fi

# 暂存当前变更
STASHED=false
if ! git diff --quiet HEAD 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
    log "📦 暂存本地变更..."
    git stash push -m "auto-stash-$(date +%s)" >> "$LOG_FILE" 2>&1 || true
    STASHED=true
fi

# 拉取远程最新变更
log "⬇️ 拉取远程变更..."
if git pull origin "$BRANCH" --rebase >> "$LOG_FILE" 2>&1; then
    log "✅ 拉取成功"
else
    log "⚠️ 拉取失败，尝试强制重置..."
    git fetch origin >> "$LOG_FILE" 2>&1
    git reset --hard "origin/$BRANCH" >> "$LOG_FILE" 2>&1 || {
        log "❌ 强制重置失败"
        exit 1
    }
fi

# 恢复暂存的变更
if [ "$STASHED" = true ]; then
    log "📤 恢复本地变更..."
    git stash pop >> "$LOG_FILE" 2>&1 || true
fi

# 添加所有变更
log "📝 添加本地变更..."
git add -A

# 检查是否有变更需要提交
if git diff --cached --quiet; then
    log "✅ 无新变更需要提交"
else
    # 提交
    commit_msg="强制同步 $(date '+%m-%d %H:%M') [云端节点]"
    git commit -m "$commit_msg" >> "$LOG_FILE" 2>&1
    log "✅ 提交成功: $commit_msg"
    
    # 推送到 GitHub
    log "⬆️ 推送到GitHub..."
    if git push origin "$BRANCH" >> "$LOG_FILE" 2>&1; then
        log "✅ 推送成功"
    else
        log "❌ 推送失败"
        exit 1
    fi
fi

# 输出同步状态
COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo "0")
LAST_COMMIT=$(git log -1 --format="%h %s" 2>/dev/null || echo "N/A")
log "📊 当前提交数: $COMMIT_COUNT"
log "📌 最新提交: $LAST_COMMIT"

log "=== 强制Git同步完成 ==="
echo "✅ 同步完成"
