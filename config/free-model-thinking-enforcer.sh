#!/bin/bash
# 免费模型思考模式强制执行器
# 在会话启动时调用，检测是否为免费模型，自动启用thinking=on

echo "=== 免费模型思考模式检测 ==="

# 获取当前模型
MODEL_PATH="/tmp/.openclaw-current-model"
touch $MODEL_PATH

# 读取当前模型（从环境变量或配置文件）
CURRENT_MODEL="${OPENCLAW_CURRENT_MODEL:-unknown}"
if [ "$CURRENT_MODEL" = "unknown" ]; then
    # 尝试从session_status获取
    if command -v openclaw >/dev/null 2>&1; then
        CURRENT_MODEL=$(openclaw session status --json 2>/dev/null | grep -o '"model":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    fi
fi

echo "当前模型: $CURRENT_MODEL"

# 免费模型列表（匹配 nvidia-build/ 前缀）
FREE_MODEL_PATTERNS=(
    "nvidia-build/z-ai/glm4.7"
    "nvidia-build/deepseek-ai/deepseek-v3.2"
    "nvidia-build/*"
)

is_free_model() {
    local model="$1"
    
    # 检查是否匹配任何免费模式
    for pattern in "${FREE_MODEL_PATTERNS[@]}"; do
        if [[ "$model" == $pattern ]] || [[ "$model" =~ $pattern ]]; then
            return 0  # 是免费模型
        fi
    done
    
    return 1  # 不是免费模型
}

# 检查是否为免费模型
if is_free_model "$CURRENT_MODEL"; then
    echo "✅ 检测到免费模型: $CURRENT_MODEL"
    echo "⚡ 根据免费模型思考原则，应启用 thinking=on"
    
    # 记录到日志
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 免费模型 $CURRENT_MODEL 应启用 thinking=on" \
        >> /root/.openclaw/workspace/memory/free-model-thinking.log
    
    # 在文件中标记应启用thinking
    echo "thinking_enabled=true" > /root/.openclaw/workspace/config/thinking-state.flag
    
    echo "已标记: 下次会话应考虑启用 thinking=on"
else
    echo "📊 付费模型或未知模型: $CURRENT_MODEL"
    echo "按需启用 thinking 模式"
    
    echo "thinking_enabled=adaptive" > /root/.openclaw/workspace/config/thinking-state.flag
fi

echo "=== 检测完成 ==="