#!/bin/bash
# 配置10个独立的nanobot实例

echo "======================================================================"
echo "🚀 配置10个HKUDS/nanobot实例"
echo "======================================================================"
echo ""

BASE_DIR="/root/.openclaw/workspace/nanobot-instances"
NANOBOT_BIN="/root/.openclaw/workspace/nanobot-env/bin/nanobot"

# 10个API Key（NVIDIA）
declare -a API_KEYS=(
    "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"
    "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"
    "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"
    "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"
    "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"
    "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"
    "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"
    "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"
    "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"
    "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"
)

# 模型分配
declare -a MODELS=(
    "stepfun-ai/step-3.5-flash"
    "stepfun-ai/step-3.5-flash"
    "deepseek-ai/deepseek-v3.2"
    "stepfun-ai/step-3.5-flash"
    "stepfun-ai/step-3.5-flash"
    "deepseek-ai/deepseek-v3.2"
    "deepseek-ai/deepseek-v3.2"
    "deepseek-ai/deepseek-v3.2"
    "z-ai/glm4.7"
    "moonshotai/kimi-k2.5"
)

# 角色分配
declare -a ROLES=(
    "fast_executor"
    "data_collector"
    "content_generator"
    "api_caller"
    "monitor"
    "deep_analyzer"
    "code_reviewer"
    "complex_solver"
    "strategy_planner"
    "quality_assurance"
)

mkdir -p "$BASE_DIR"

for i in {0..9}; do
    idx=$((i+1))
    NB_ID="nanobot-${idx}"
    NB_DIR="$BASE_DIR/$NB_ID"
    PORT=$((18800 + idx))
    
    echo "配置 $NB_ID..."
    
    # 创建工作目录
    mkdir -p "$NB_DIR/workspace"
    
    # 创建配置
    cat > "$NB_DIR/config.json" <>OF
{
  "providers": {
    "nvidia": {
      "apiKey": "${API_KEYS[$i]}",
      "apiBase": "https://integrate.api.nvidia.com/v1"
    }
  },
  "agents": {
    "defaults": {
      "model": "${MODELS[$i]}",
      "provider": "nvidia"
    }
  },
  "tools": {
    "restrictToWorkspace": true
  }
}
EOF
    
    # 创建启动脚本
    cat > "$NB_DIR/start.sh" <>OF
#!/bin/bash
cd "$NB_DIR"
export NANOBOT_ROLE="${ROLES[$i]}"
export NANOBOT_ID="$NB_ID"
$NANOBOT_BIN gateway -w "$NB_DIR/workspace" -c "$NB_DIR/config.json" -p $PORT
EOF
    chmod +x "$NB_DIR/start.sh"
    
    echo "  ✅ $NB_ID 配置完成 (端口: $PORT, 模型: ${MODELS[$i]})"
done

echo ""
echo "======================================================================"
echo "✅ 10个nanobot实例配置完成！"
echo "======================================================================"
echo ""
echo "启动所有实例："
echo "  bash $BASE_DIR/start-all.sh"
echo ""
echo "查看状态："
echo "  ps aux | grep nanobot-gateway"
echo ""
