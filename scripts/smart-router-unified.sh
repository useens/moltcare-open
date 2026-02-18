#!/bin/bash
# 统一智能路由系统 - 适配 nvidia-build 模型集
# 根据任务类型和复杂度自动选择模型和thinking模式

USER_INPUT="$1"
CURRENT_MODEL="${2:-nvidia-build/stepfun-ai/step-3.5-flash}"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🤖 智能路由分析${NC}"
echo "=================="
echo "输入: $USER_INPUT"
echo "当前模型: $CURRENT_MODEL"
echo ""

# 调用难度评估和模型推荐脚本
EVAL_RESULT=$(python3 /root/.openclaw/workspace/scripts/assess-difficulty.py "$USER_INPUT" 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "⚠️  评估失败，使用默认模型"
    echo "建议: nvidia-build/stepfun-ai/step-3.5-flash"
    echo "thinking: on"
    exit 0
fi

# 解析结果
DIFFICULTY=$(echo "$EVAL_RESULT" | grep "难度级别" | cut -d: -f2 | xargs)
RECOMMENDED_MODEL=$(echo "$EVAL_RESULT" | grep "推荐模型" | cut -d: -f2 | xargs)
THINKING_MODE=$(echo "$EVAL_RESULT" | grep "Thinking模式" | cut -d: -f2 | xargs)
REASON=$(echo "$EVAL_RESULT" | grep "原因" | cut -d: -f2- | xargs)

echo -e "${YELLOW}💡 评估结果${NC}"
echo "=================="
echo "难度级别: L$DIFFICULTY"
echo "推荐模型: $RECOMMENDED_MODEL"
echo "Thinking: $THINKING_MODE"
echo "原因: $REASON"
echo ""

# 检查是否与当前模型相同
if [ "$RECOMMENDED_MODEL" = "$CURRENT_MODEL" ]; then
    echo "{\"action\": \"none\", \"reason\": \"当前模型已是最优选择\"}"
    exit 0
fi

# 输出建议（供调用脚本使用）
echo "{\"action\": \"suggest\", \"current_model\": \"$CURRENT_MODEL\", \"suggested_model\": \"$RECOMMENDED_MODEL\", \"thinking\": \"$THINKING_MODE\", \"difficulty\": \"$DIFFICULTY\", \"reason\": \"$REASON\"}"
