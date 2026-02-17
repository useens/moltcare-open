#!/bin/bash
# Smart Router Wrapper - 统一入口
# 优先调用服务，失败时回退到本地脚本

TASK="$1"
CURRENT_MODEL="${2:-step}"
API_URL="127.0.0.1:8766"

# 1. 尝试服务调用（最快）
if curl -s --max-time 2 "http://${API_URL}/health" > /dev/null 2>&1; then
    # 服务可用，使用客户端（注意参数顺序: TASK, SIGNAL, DIFFICULTY, CURRENT_MODEL）
    # 这里传递: TASK + 空SIGNAL + 空DIFFICULTY + CURRENT_MODEL
    RESULT=$(./scripts/smart-router-client.sh "$TASK" "" "" "$CURRENT_MODEL" 2>/dev/null)
    if [ $? -eq 0 ] && echo "$RESULT" | python3 -c "import sys, json; j=json.load(sys.stdin); exit(0 if j.get('success') else 1)" 2>/dev/null; then
        # 服务返回成功
        echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
        exit 0
    fi
fi

# 2. 服务不可用或失败，回退到本地统一脚本
./scripts/smart-router-unified.sh "$TASK" "$CURRENT_MODEL"
