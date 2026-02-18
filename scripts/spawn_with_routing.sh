#!/bin/bash
# 子代理智能路由包装器
# 在 sessions_spawn 之前自动选择最优模型和thinking模式

USER_TASK="$1"
AGENT_ID="${2:-main}"

echo "=== 子代理智能路由 ==="
echo "任务: $USER_TASK"
echo "目标Agent: $AGENT_ID"
echo ""

# 调用统一路由脚本（输出JSON在最后一行）
ROUTING_RESULT=$(/root/.openclaw/workspace/scripts/smart-router-unified.sh "$USER_TASK" "unknown" 2>/dev/null)

# 提取最后一行JSON
JSON_LINE=$(echo "$ROUTING_RESULT" | tail -n1)

# 解析JSON
SUGGESTED_MODEL=$(echo "$JSON_LINE" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('suggested_model',''))" 2>/dev/null)
THINKING_MODE=$(echo "$JSON_LINE" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('thinking',''))" 2>/dev/null)
REASON=$(echo "$JSON_LINE" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('reason',''))" 2>/dev/null)

echo ""
echo "=== 路由决策 ==="
echo "模型: $SUGGESTED_MODEL"
echo "Thinking: $THINKING_MODE"
echo "原因: $REASON"
echo ""

# 模型名称已经是完整路径，直接使用
FULL_MODEL="$SUGGESTED_MODEL"

# 输出sessions_spawn命令（方便调用）
echo "=== 生成spawn命令 ==="
echo "openclaw sessions spawn \\"
echo "  --task=\"$USER_TASK\" \\"
echo "  --agent=$AGENT_ID \\"
echo "  --model=$FULL_MODEL \\"
echo "  --thinking=$THINKING_MODE"
