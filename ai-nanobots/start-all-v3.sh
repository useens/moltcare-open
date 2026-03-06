#!/bin/bash
# 启动所有 Nanobot V3

cd /root/.openclaw/workspace

# 定义10个nanobot的配置
declare -A BOTS=(
    ["nanobot-1"]="研究员:researcher:research,data_analysis,search"
    ["nanobot-2"]="架构师:architect:design,architecture,planning"
    ["nanobot-3"]="工程师:engineer:coding,debugging,testing"
    ["nanobot-4"]="安全专家:security:security,audit,pentest"
    ["nanobot-5"]="分析师:analyst:analysis,reporting,metrics"
    ["nanobot-6"]="决策分析师:decision:decision,evaluation,strategy"
    ["nanobot-7"]="代码审查员:reviewer:code_review,quality,standards"
    ["nanobot-8"]="运维专家:ops:ops,monitoring,deployment"
    ["nanobot-9"]="战略规划师:strategist:strategy,planning,roadmap"
    ["nanobot-10"]="协调者:coordinator:coordination,communication,sync"
)

echo "🚀 启动 Nanobot V3 集群..."
echo ""

# 创建日志目录
mkdir -p /root/.openclaw/workspace/data/neural_hub/logs

# 启动每个bot
for bot_id in nanobot-{1..10}; do
    config="${BOTS[$bot_id]}"
    if [ -n "$config" ]; then
        IFS=':' read -r name role capabilities <<< "$config"
        
        echo "  启动 $bot_id ($name)..."
        
        nohup python3 ai-nanobots/nanobot-v3.py \
            --id "$bot_id" \
            --name "$name" \
            --role "$role" \
            > /root/.openclaw/workspace/data/neural_hub/logs/${bot_id}.log 2>&1 &
        
        echo $! > /root/.openclaw/workspace/data/neural_hub/${bot_id}.pid
        
        # 错开启动时间
        sleep 2
    fi
done

echo ""
echo "✅ Nanobot V3 集群已启动"
echo "   查看日志: tail -f data/neural_hub/logs/nanobot-*.log"
echo ""
echo "停止命令: ./ai-nanobots/stop-all-v3.sh"
