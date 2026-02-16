#!/bin/bash
# 子代理智能路由包装器
# 在 sessions_spawn 之前自动选择最优模型和thinking模式

USER_TASK="$1"
AGENT_ID="${2:-main}"

echo "=== 子代理智能路由 ==="
echo "任务: $USER_TASK"
echo "目标Agent: $AGENT_ID"
echo ""

# 调用统一路由脚本
ROUTING_RESULT=$(/root/.openclaw/workspace/scripts/smart-router-unified.sh "$USER_TASK" "unknown")

# 提取建议模型和thinking模式
SUGGESTED_MODEL=$(echo "$ROUTING_RESULT" | grep "建议:" | awk '{print $2}')
THINKING_MODE=$(echo "$ROUTING_RESULT" | grep "Thinking模式:" | awk '{print $2}')
REASON=$(echo "$ROUTING_RESULT" | grep "原因:" | cut -d: -f2-)

echo ""
echo "=== 路由决策 ==="
echo "模型: $SUGGESTED_MODEL"
echo "Thinking: $THINKING_MODE"
echo "原因: $REASON"
echo ""

# 映射模型名称到完整路径
case "$SUGGESTED_MODEL" in
    "ds")
        FULL_MODEL="nvidia-build/deepseek-ai/deepseek-v3.2"
        ;;
    "kimi")
        FULL_MODEL="nvidia-build/moonshotai/kimi-k2.5"
        ;;
    "glm")
        FULL_MODEL="nvidia-build/z-ai/glm4.7"
        ;;
    "k2p5")
        FULL_MODEL="kimi-coding/k2p5"
        ;;
    *)
        FULL_MODEL="nvidia-build/deepseek-ai/deepseek-v3.2"
        ;;
esac

# 输出sessions_spawn命令（方便调用）
echo "=== 生成spawn命令 ==="
echo "openclaw sessions spawn \\"
echo "  --task=\"$USER_TASK\" \\"
echo "  --agent=$AGENT_ID \\"
echo "  --model=$FULL_MODEL \\"
echo "  --thinking=$THINKING_MODE"
