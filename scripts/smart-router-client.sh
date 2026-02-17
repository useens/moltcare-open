#!/bin/bash
# Smart Router Client - 通过 HTTP API 调用智能路由
# 用法: smart-router-client.sh "任务描述" [signal] [difficulty]

TASK="$1"
SIGNAL="$2"
DIFFICULTY="$3"
CURRENT_MODEL="${4:-step}"
API_URL="http://127.0.0.1:8766"

if [ -z "$TASK" ]; then
    echo "用法: $0 \"任务描述\" [signal] [difficulty] [current_model]"
    echo "示例: $0 \"帮我写Python脚本\""
    echo "示例: $0 \"重要任务\" 9"
    exit 1
fi

# 构建JSON请求体
JSON_BODY="{\"task\":\"$TASK\""
if [ -n "$SIGNAL" ]; then
    JSON_BODY="$JSON_BODY, \"signal\":$SIGNAL"
fi
if [ -n "$DIFFICULTY" ]; then
    JSON_BODY="$JSON_BODY, \"difficulty\":\"$DIFFICULTY\""
fi
if [ -n "$CURRENT_MODEL" ] && [ "$CURRENT_MODEL" != "step" ]; then
    JSON_BODY="$JSON_BODY, \"current_model\":\"$CURRENT_MODEL\""
fi
JSON_BODY="$JSON_BODY}"

# 调用路由服务
RESPONSE=$(curl -s -X POST "$API_URL/route" \
    -H "Content-Type: application/json" \
    -d "$JSON_BODY")

# 检查错误
if echo "$RESPONSE" | grep -q '"error"'; then
    echo "路由失败: $RESPONSE" >&2
    exit 1
fi

# 输出JSON结果
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
