#!/bin/bash
# 优化版智能路由系统
# 集成：路由 + 分级 + 确认 + 偏好学习

USER_INPUT="$1"
CURRENT_MODEL="${2:-ds}"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 智能路由分析${NC}"
echo "=================="
echo ""

# 第一步：检查是否有强偏好
PREFERENCE_MATCH=""
for pattern in python_code image_analysis chinese_text; do
    if echo "$USER_INPUT" | grep -qiE "Python|代码|函数"; then
        if [ "$pattern" = "python_code" ]; then
            PREFERENCE_MATCH="k2p5"
            PREFERENCE_CONFIDENCE="high"
        fi
    elif echo "$USER_INPUT" | grep -qiE "图片|截图|分析"; then
        if [ "$pattern" = "image_analysis" ]; then
            PREFERENCE_MATCH="kimi"
            PREFERENCE_CONFIDENCE="high"
        fi
    elif echo "$USER_INPUT" | grep -qiE "中文|文案|翻译"; then
        if [ "$pattern" = "chinese_text" ]; then
            PREFERENCE_MATCH="glm"
            PREFERENCE_CONFIDENCE="high"
        fi
    fi
done

# 第二步：运行自动路由
ROUTING_RESULT=$(/root/.openclaw/workspace/scripts/auto-router.sh "$USER_INPUT" "$CURRENT_MODEL")
ACTION=$(echo "$ROUTING_RESULT" | grep -o '"action": "[^"]*"' | cut -d'"' -f4)

if [ "$ACTION" = "none" ]; then
    echo -e "${GREEN}✓${NC} 当前模型已是最优选择 ($CURRENT_MODEL)"
    exit 0
fi

SUGGESTED_MODEL=$(echo "$ROUTING_RESULT" | grep -o '"suggested_model": "[^"]*"' | cut -d'"' -f4)
REASON=$(echo "$ROUTING_RESULT" | grep -o '"reason": "[^"]*"' | cut -d'"' -f4)
CONFIDENCE=$(echo "$ROUTING_RESULT" | grep -o '"confidence": [0-9]*' | grep -o '[0-9]*')

# 第三步：k2p5分级（如果需要）
THINKING_INFO=""
if [ "$SUGGESTED_MODEL" = "k2p5" ]; then
    DIFFICULTY_RESULT=$(/root/.openclaw/workspace/scripts/k2p5-smart-eval.sh "$USER_INPUT")
    THINKING_MODE=$(echo "$DIFFICULTY_RESULT" | grep -o '"thinking_mode": "[^"]*"' | cut -d'"' -f4)
    LEVEL=$(echo "$DIFFICULTY_RESULT" | grep -o '"level": "[^"]*"' | cut -d'"' -f4)
    THINKING_INFO=" | $LEVEL | thinking:$THINKING_MODE"
fi

# 第四步：显示建议
echo -e "${YELLOW}💡 建议切换${NC}"
echo "=================="
echo "当前: $CURRENT_MODEL"
echo "建议: $SUGGESTED_MODEL$THINKING_INFO"
echo "原因: $REASON"
echo "置信度: $CONFIDENCE%"

# 第五步：检查强偏好
if [ -n "$PREFERENCE_MATCH" ] && [ "$PREFERENCE_MATCH" = "$SUGGESTED_MODEL" ]; then
    echo ""
    echo -e "${GREEN}✓${NC} 符合您的使用偏好，自动应用中..."
    echo "执行: 切换到 $SUGGESTED_MODEL"
    if [ "$SUGGESTED_MODEL" = "k2p5" ]; then
        echo "执行: thinking $THINKING_MODE"
    fi
    exit 0
fi

# 第六步：请求确认
echo ""
echo -e "${YELLOW}确认切换?${NC} [y/n/always]"
echo "y - 确认切换"
echo "n - 保持当前"
echo "always - 记住此偏好，以后自动应用"
