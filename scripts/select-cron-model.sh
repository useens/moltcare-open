#!/bin/bash
# Cron任务智能路由选择脚本
# 根据任务类型和Signal评分选择最优模型

TASK_NAME="$1"
SIGNAL_LEVEL="${2:-0}"  # Signal评分（如果有）

echo "=== Cron智能路由 ===" 
echo "任务: $TASK_NAME"
echo "Signal: $SIGNAL_LEVEL"
echo ""

# Signal评分路由
if [ "$SIGNAL_LEVEL" -ge 9 ]; then
    echo "model: kimi-coding/k2p5"
    echo "thinking: high"
    echo "reason: Signal $SIGNAL_LEVEL - 高价值内容，使用最强模型"
    exit 0
elif [ "$SIGNAL_LEVEL" -ge 7 ]; then
    echo "model: nvidia-build/moonshotai/kimi-k2.5"
    echo "thinking: on"
    echo "reason: Signal $SIGNAL_LEVEL - 中高价值，256k上下文处理"
    exit 0
fi

# 任务类型路由
case "$TASK_NAME" in
    "evolution-intelligence")
        echo "model: nvidia-build/moonshotai/kimi-k2.5"
        echo "thinking: on"
        echo "reason: 情报收集，256k适合处理大量数据"
        ;;
    
    "moltbook-unified-scan")
        echo "model: nvidia-build/moonshotai/kimi-k2.5"
        echo "thinking: on"
        echo "reason: Moltbook扫描，256k适合长文档"
        ;;
    
    "evolution-knowledge")
        echo "model: nvidia-build/deepseek-ai/deepseek-v3.2"
        echo "thinking: on"
        echo "reason: 知识内化，ds推理能力最强"
        ;;
    
    "evolution-deep-learning")
        echo "model: kimi-coding/k2p5"
        echo "thinking: high"
        echo "reason: 深度学习（架构级），最强模型"
        ;;
    
    "unified-monitor-check"|"unified-maintenance-daily")
        echo "model: nvidia-build/deepseek-ai/deepseek-v3.2"
        echo "thinking: off"
        echo "reason: 生产任务，低成本执行"
        ;;
    
    *)
        echo "model: nvidia-build/deepseek-ai/deepseek-v3.2"
        echo "thinking: off"
        echo "reason: 默认模型"
        ;;
esac
