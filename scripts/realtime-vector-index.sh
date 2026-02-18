#!/bin/bash
# 实时向量索引 - 用于重要记忆（Signal≥8）
# 用法: ./realtime-vector-index.sh "内容" "来源"

CONTENT="$1"
SOURCE="${2:-manual}"

if [ -z "$CONTENT" ]; then
    echo "用法: $0 '内容' '来源'"
    exit 1
fi

python3 /root/.openclaw/workspace/scripts/vector-memory-indexer.py \
    --content "$CONTENT" \
    --source "$SOURCE"
