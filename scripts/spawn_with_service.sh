#!/bin/bash
# 子代理智能路由包装器 (Service Version)
# 使用智能路由HTTP服务获取决策，高效无阻塞

USER_TASK="$1"
AGENT_ID="${2:-main}"

echo "=== 子代理智能路由 (Service Mode) ==="
echo "任务: $USER_TASK"
echo "目标Agent: $AGENT_ID"
echo ""

# 调用智能路由服务
ROUTING_JSON=$(./scripts/smart-router-client.sh "$USER_TASK" "" "" "unknown" 2>/dev/null)

# 检查服务是否响应
if [ $? -ne 0 ] || echo "$ROUTING_JSON" | grep -q '"error"'; then
    echo "[WARN] 智能路由服务不可用，回退到本地脚本..."
    ROUTING_JSON=$(./scripts/smart-router-unified.sh "$USER_TASK" "unknown" 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "[ERROR] 本地路由也失败，使用默认配置"
        SUGGESTED_MODEL="ds"
        THINKING_MODE="on"
        REASON="默认配置（服务与本地均失败）"
    else
        # 解析unified.sh输出（假设格式固定）
        SUGGESTED_MODEL=$(echo "$ROUTING_JSON" | grep "建议:" | awk '{print $2}')
        THINKING_MODE=$(echo "$ROUTING_JSON" | grep "Thinking模式:" | awk '{print $2}')
        REASON=$(echo "$ROUTING_JSON" | grep "原因:" | cut -d: -f2-)
    fi
else
    # 解析服务JSON响应
    SUGGESTED_MODEL=$(echo "$ROUTING_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['model'])" 2>/dev/null)
    THINKING_MODE=$(echo "$ROUTING_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['thinking'])" 2>/dev/null)
    REASON=$(echo "$ROUTING_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['reason'])" 2>/dev/null)

    # 解码Unicode转义（可选）
    if echo "$REASON" | grep -q '\\u'; then
        REASON=$(echo "$REASON" | python3 -c "import sys, json; print(json.load(sys.stdin)['reason'])" 2>/dev/null)
    fi
fi

echo ""
echo "=== 路由决策 ==="
echo "模型: $SUGGESTED_MODEL"
echo "Thinking: $THINKING_MODE"
echo "原因: $REASON"
echo ""

# 映射模型别名到完整路径
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
    "step")
        FULL_MODEL="nvidia-build/stepfun-ai/step-3.5-flash"
        ;;
    *)
        FULL_MODEL="nvidia-build/deepseek-ai/deepseek-v3.2"
        ;;
esac

# 输出 sessions_spawn 命令
echo "=== 生成 spawn 命令 ==="
echo "openclaw sessions spawn \\"
echo "  --task=\"$USER_TASK\" \\"
echo "  --agent=$AGENT_ID \\"
echo "  --model=$FULL_MODEL \\"
echo "  --thinking=$THINKING_MODE"
echo ""
echo "提示: 复制上面的命令并执行，或使用管道:"
echo "eval \$(./scripts/spawn_with_service.sh \"$USER_TASK\")"
