#!/bin/bash
# 智能Git同步脚本 - 只在有实际变更时同步，忽略临时文件
# 用途：优化Git提交频率，避免临时文件污染历史

set -e

WORKSPACE="/root/.openclaw/workspace"
cd "$WORKSPACE"

# 清理临时文件（不提交它们）
cleanup_temp_files() {
    # 向量存储临时事务文件
    find data/vector_memory -name "*.txn" -type f -delete 2>/dev/null || true
    find data/vector_memory -path "*/_transactions/*" -type f -delete 2>/dev/null || true
    
    # 重置Git对这些临时文件的跟踪
    git checkout -- data/vector_memory/ 2>/dev/null || true
}

# 检查是否有值得提交的实际变更（排除临时文件）
has_meaningful_changes() {
    # 先清理临时文件
    cleanup_temp_files
    
    # 检查是否有剩余的非忽略文件变更
    if git diff --quiet HEAD && git diff --cached --quiet; then
        return 1  # 没有变更
    fi
    
    # 获取变更文件列表，排除临时文件/日志等
    local changed_files=$(git status --porcelain | grep -v "^??" | awk '{print $2}' | grep -v -E '\.(log|tmp|txn)$' | grep -v "data/vector_memory" | head -20)
    
    if [ -z "$changed_files" ]; then
        return 1  # 只有临时文件变更
    fi
    
    return 0  # 有实际变更
}

# 主逻辑
if ! has_meaningful_changes; then
    # 没有实际变更，静默退出
    exit 0
fi

# 有实际变更，执行同步
echo "检测到实际文件变更，执行Git同步..."
bash "$WORKSPACE/scripts/forced-git-sync.sh"
