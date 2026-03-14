#!/bin/bash
# Hourly Template Mining - Sub Agent Entry Point
# 作为子 Agent 每小时执行的入口

WORKSPACE="$HOME/.openclaw/workspace/moltcare-open"
RESEARCH_DIR="$WORKSPACE/research"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y-%m-%d)
HOUR=$(date +%H)

echo "🦞 [子 Agent] 每小时模板挖掘执行"
echo "时间: $(date)"
echo ""

# 搜索关键词轮换
SEARCH_KEYWORDS=(
  "Anthropic prompt engineering"
  "OpenAI GPT-4 system prompt"
  "CrewAI agent role"
  "LangChain hub prompt"
  "AutoGPT agent prompts"
  "LLM agent framework"
  "Claude system prompt"
  "AI agent cognitive"
)

KEYWORD_INDEX=$((10#$HOUR % ${#SEARCH_KEYWORDS[@]}))
SELECTED_KEYWORD="${SEARCH_KEYWORDS[$KEYWORD_INDEX]}"

echo "关键词: $SELECTED_KEYWORD"
echo ""

# 使用 GitHub 搜索（带缓存避免重复）
CACHE_FILE="$RESEARCH_DIR/.cache/last_search_${HOUR}"
mkdir -p "$RESEARCH_DIR/.cache"

if [ -f "$CACHE_FILE" ] && [ $(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0))) -lt 3600 ]; then
    echo "使用缓存结果 (一小时内已搜索)"
    cat "$CACHE_FILE"
else
    # 执行搜索
    SEARCH_QUERY=$(echo "$SELECTED_KEYWORD" | tr ' ' '+')
    RESPONSE=$(curl -sL "https://api.github.com/search/repositories?q=${SEARCH_QUERY}&sort=updated&order=desc&per_page=3" 2>/dev/null || echo '{"items":[]}')
    
    echo "$RESPONSE" > "$CACHE_FILE"
    
    # 解析并显示结果
    REPO_COUNT=$(echo "$RESPONSE" | grep -o '"full_name"' | wc -l)
    echo "发现: $REPO_COUNT 个仓库"
    
    if [ "$REPO_COUNT" -gt 0 ]; then
        echo "$RESPONSE" | grep '"full_name"' | head -5 | sed 's/.*: "\([^"]*\)".*/  - \1/'
    fi
fi

echo ""
echo "✅ 执行完成"
echo "下次执行: 1小时后"
echo ""
echo "$(date): 每小时挖掘完成，关键词='$SELECTED_KEYWORD'" >> "$RESEARCH_DIR/hourly-activity.log"
