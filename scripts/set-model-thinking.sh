#!/bin/bash
# 自动设置模型对应的thinking模式
# 用法: source set-model-thinking.sh <model_name>

MODEL_NAME=$1

case $MODEL_NAME in
    "ds"|"glm"|"kimi")
        echo "✅ 免费模型 $MODEL_NAME，设置 thinking on"
        # 在实际环境中这里会调用 thinking on
        echo "THINKING_MODE=on"
        ;;
    "k2p5")
        echo "✅ 付费模型 k2p5，设置 thinking off（默认）"
        echo "THINKING_MODE=off"
        ;;
    *)
        echo "❌ 未知模型: $MODEL_NAME"
        exit 1
        ;;
esac
