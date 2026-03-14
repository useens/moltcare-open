#!/bin/bash
# MoltCare Hourly Search - 只搜索和保存

HOUR=$(date +%H)
DATE=$(date +%Y%m%d)

WORK_DIR="$HOME/.openclaw/workspace/moltcare-open/research/daily/$DATE"
mkdir -p "$WORK_DIR/raw"

LOG_FILE="$WORK_DIR/raw/search_${HOUR}.log"

echo "🦞 Hourly Search & Save" | tee "$LOG_FILE"
echo "时间: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 24小时关键词轮换
declare -A KEYWORDS=(
    ["00"]="awesome-chatgpt-prompts"
    ["01"]="anthropic-cookbook"
    ["02"]="openai-cookbook"
    ["03"]="langchain-hub"
    ["04"]="crewai-examples"
    ["05"]="autogpt-prompts"
    ["06"]="system-prompts-leaks"
    ["07"]="prompt-engineering-guide"
    ["08"]="ai-agent-patterns"
    ["09"]="multi-agent-framework"
    ["10"]="awesome-chatgpt-prompts-zh"
    ["11"]="obsidian-templates"
    ["12"]="para-method-templates"
    ["13"]="zettelkasten-templates"
    ["14"]="devcontainer-templates"
    ["15"]="dotfiles-manager"
    ["16"]="dify-workflow"
    ["17"]="n8n-ai-workflow"
    ["18"]="model-context-protocol"
    ["19"]="ai-digest-automation"
    ["20"]="reddit-ai-prompts"
    ["21"]="hackernews-ai-tools"
    ["22"]="product-hunt-ai"
    ["23"]="papers-with-code-llm"
)

KEYWORD="${KEYWORDS[$HOUR]:-agent-template}"

echo "🔍 [$HOUR:00] 关键词: $KEYWORD" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 执行搜索
RESPONSE=$(curl -sL "https://api.github.com/search/repositories?q=${KEYWORD}&sort=stars&order=desc&per_page=10" 2>/dev/null)

# 保存原始结果
echo "$RESPONSE" > "$WORK_DIR/raw/github_${HOUR}.json"

# 解析并生成摘要
SUMMARY=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data.get('items', [])
    total = data.get('total_count', 0)
    
    high_value = sum(1 for item in items if item['stargazers_count'] > 1000)
    
    print(f'总发现: {total}')
    print(f'高价值(>1k⭐): {high_value}')
    print()
    for item in items[:5]:
        stars = item['stargazers_count']
        icon = '🔥' if stars > 1000 else '⭐' if stars > 100 else '•'
        print(f\"{icon} {item['full_name']} ({stars}⭐)\")
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null)

echo "$SUMMARY" | tee -a "$LOG_FILE"

# 如果有高价值发现，单独标记
HIGH_COUNT=$(echo "$SUMMARY" | grep -o "高价值.*: [0-9]*" | grep -o "[0-9]*" || echo "0")
if [ "$HIGH_COUNT" -gt 0 ]; then
    echo "$(date): $HOUR:00 - $KEYWORD - $HIGH_COUNT 高价值" >> "$WORK_DIR/high_value_markers.txt"
    echo "🔥 标记 $HIGH_COUNT 个高价值发现" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "✅ 已保存到: $WORK_DIR/raw/github_${HOUR}.json" | tee -a "$LOG_FILE"
echo "📊 每日分析报告将在 23:00 生成" | tee -a "$LOG_FILE"
