#!/bin/bash
# 条件Git同步脚本 - 仅在文件变更时执行

set -e

cd /root/.openclaw/workspace

# 检查是否有文件变更
if git diff --quiet HEAD && git diff --cached --quiet; then
    # 没有变更，静默退出
    exit 0
fi

# 有变更，执行同步
echo "检测到文件变更，执行Git同步..."
bash /root/.openclaw/workspace/scripts/forced-git-sync.sh
