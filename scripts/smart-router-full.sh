#!/bin/bash
# 智能路由+分级完整集成脚本
# 自动判断模型和thinking模式

USER_INPUT="$1"
CURRENT_MODEL="${2:-ds}"

echo "=== 智能路由分析 ==="
echo "输入: $USER_INPUT"
echo "当前模型: $CURRENT_MODEL"
echo ""

# 第一步：路由决策
ROUTING_RESULT=$(/root/.openclaw/workspace/scripts/auto-router.sh "$USER_INPUT" "$CURRENT_MODEL")
ACTION=$(echo "$ROUTING_RESULT" | grep -o '"action": "[^"]*"' | cut -d'"' -f4)

if [ "$ACTION" = "none" ]; then
    echo "决策: 保持当前模型"
    echo "原因: $(echo "$ROUTING_RESULT" | grep -o '"reason": "[^"]*"' | cut -d'"' -f4)"
    exit 0
fi

SUGGESTED_MODEL=$(echo "$ROUTING_RESULT" | grep -o '"suggested_model": "[^"]*"' | cut -d'"' -f4)
REASON=$(echo "$ROUTING_RESULT" | grep -o '"reason": "[^"]*"' | cut -d'"' -f4)
CONFIDENCE=$(echo "$ROUTING_RESULT" | grep -o '"confidence": [0-9]*' | grep -o '[0-9]*')

echo "建议切换至: $SUGGESTED_MODEL"
echo "原因: $REASON"
echo "置信度: $CONFIDENCE%"
echo ""

# 第二步：如果是k2p5，进行难度分级
if [ "$SUGGESTED_MODEL" = "k2p5" ]; then
    echo "=== k2p5智能分级 ==="
    DIFFICULTY_RESULT=$(/root/.openclaw/workspace/scripts/k2p5-smart-eval.sh "$USER_INPUT")
    THINKING_MODE=$(echo "$DIFFICULTY_RESULT" | grep -o '"thinking_mode": "[^"]*"' | cut -d'"' -f4)
    LEVEL=$(echo "$DIFFICULTY_RESULT" | grep -o '"level": "[^"]*"' | cut -d'"' -f4)
    
    echo "难度级别: $LEVEL"
    echo "Thinking模式: $THINKING_MODE"
    echo ""
    echo "建议操作:"
    echo "1. 切换到 k2p5"
    echo "2. 设置 thinking $THINKING_MODE"
else
    echo "建议操作:"
    echo "1. 切换到 $SUGGESTED_MODEL"
    echo "2. 使用默认配置（reasoning已开启）"
fi

echo ""
echo "等待用户确认 (y/n)..."
