#!/bin/bash
# 强制Git同步脚本 - 云端节点静默同步
# 用途：执行真正的 commit + push，只在有实际变更时调用

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

log "=== Git同步开始 ==="

# 检查Git仓库
if [ ! -d ".git" ]; then
    log "❌ 不是Git仓库"
    exit 1
fi

BRANCH=$(git branch --show-current 2>/dev/null || echo "master")
log "当前分支: $BRANCH"

# 拉取远程最新（避免冲突）
log "⬇️ 拉取远程变更..."
if git pull origin "$BRANCH" --rebase >> "$LOG_FILE" 2>&1; then
    log "✅ 拉取成功"
else
    log "⚠️ 拉取有冲突，尝试自动解决..."
    git fetch origin >> "$LOG_FILE" 2>&1
    git rebase --abort 2>/dev/null || true
    git reset --hard "origin/$BRANCH" >> "$LOG_FILE" 2>&1
fi

# 添加所有变更
git add -A

# 生成提交摘要（基于实际变更）
get_change_summary() {
    local summary=""
    local changed=$(git diff --cached --name-only | head -5)
    local count=$(git diff --cached --name-only | wc -l)
    
    # 检测变更类型
    if echo "$changed" | grep -q "\.py$"; then
        summary="代码更新"
    elif echo "$changed" | grep -q "\.md$"; then
        summary="文档更新"
    elif echo "$changed" | grep -q "config/"; then
        summary="配置更新"
    elif echo "$changed" | grep -q "memory/"; then
        summary="记忆更新"
    else
        summary="文件更新"
    fi
    
    if [ "$count" -gt 5 ]; then
        summary="$summary +$((count-5))文件"
    fi
    
    echo "$summary"
}

# 检查是否有变更需要提交
if git diff --cached --quiet; then
    log "✅ 无新变更需要提交"
else
    # 提交
    SUMMARY=$(get_change_summary)
    commit_msg="sync: $SUMMARY | $(date '+%Y-%m-%d_%H:%M')"
    git commit -m "$commit_msg" >> "$LOG_FILE" 2>&1
    log "✅ 提交: $commit_msg"
    
    # 推送到 GitHub
    log "⬆️ 推送到GitHub..."
    if git push origin "$BRANCH" >> "$LOG_FILE" 2>&1; then
        log "✅ 推送成功"
    else
        log "❌ 推送失败"
        exit 1
    fi
fi

log "=== Git同步完成 ==="
echo "✅ 同步完成"
