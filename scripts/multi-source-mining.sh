#!/bin/bash
# MoltCare Multi-Source Template Mining
# GitHub + Web Direct Fetch + APIs

HOUR=$(date +%H)
DATE=$(date +%Y%m%d)

# 创建工作目录
WORK_DIR="$HOME/.openclaw/workspace/moltcare-open/research/hourly/$DATE"
mkdir -p "$WORK_DIR"

LOG_FILE="$WORK_DIR/search_${HOUR}.log"
REPORT_FILE="$WORK_DIR/report_${HOUR}.md"

echo "🦞 Multi-Source Template Mining" | tee "$LOG_FILE"
echo "时间: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 定义搜索源
# 格式: 小时|源类型|名称|搜索命令/URL
declare -A SEARCH_TASKS=(
    # GitHub 官方资源
    ["00"]="github|Anthropic Cookbook|curl -sL 'https://api.github.com/search/repositories?q=anthropics/prompt-eng-interactive-tutorial&per_page=5'"
    ["02"]="github|OpenAI Cookbook|curl -sL 'https://api.github.com/search/repositories?q=openai/openai-cookbook&per_page=5'"
    ["04"]="github|LangChain Hub|curl -sL 'https://api.github.com/search/repositories?q=langchain-ai/langchain-hub&per_page=5'"
    ["06"]="github|Awesome Prompts|curl -sL 'https://api.github.com/search/repositories?q=awesome-chatgpt-prompts+stars:>1000&sort=stars&per_page=5'"
    ["08"]="github|Agent Frameworks|curl -sL 'https://api.github.com/search/repositories?q=crewai+autogpt+stars:>500&sort=stars&per_page=5'"
    ["10"]="github|System Prompts|curl -sL 'https://api.github.com/search/repositories?q=system-prompts-leaks&per_page=5'"
    
    # Web 文档直接抓取
    ["01"]="web|Anthropic Docs|curl -sL 'https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering' | grep -oP '(?<=<h[12]>)[^<]+' | head -20"
    ["03"]="web|OpenAI Docs|curl -sL 'https://platform.openai.com/docs/guides/prompt-engineering' 2>/dev/null | grep -oP '(?<=<h[12]>)[^<]+' | head -20 || echo 'OpenAI docs fetch limited'"
    
    # Awesome 合集
    ["12"]="github|Awesome LLM|curl -sL 'https://api.github.com/search/repositories?q=awesome-llm+awesome-prompts&sort=stars&per_page=5'"
    ["14"]="github|Productivity Templates|curl -sL 'https://api.github.com/search/repositories?q=obsidian-templates+stars:>100&sort=stars&per_page=5'"
    
    # 配置文件/脚手架
    ["16"]="github|Dev Containers|curl -sL 'https://api.github.com/search/repositories?q=devcontainer+templates+stars:>50&sort=stars&per_page=5'"
    
    # 中文资源
    ["18"]="github|Chinese Resources|curl -sL 'https://api.github.com/search/repositories?q=chatgpt-prompts-zh+awesome-gpt-chinese&sort=stars&per_page=5'"
    
    # 其他时段用 GitHub 通用搜索
    ["05"]="github|Microsoft Promptflow|curl -sL 'https://api.github.com/search/repositories?q=microsoft/promptflow&per_page=5'"
    ["07"]="github|Prompt Engineering|curl -sL 'https://api.github.com/search/repositories?q=prompt-engineering-guide+stars:>500&sort=stars&per_page=5'"
    ["09"]="github|Agent Patterns|curl -sL 'https://api.github.com/search/repositories?q=ai-agent-patterns+cognitive-architecture&sort=stars&per_page=5'"
    ["11"]="github|System Prompt Design|curl -sL 'https://api.github.com/search/repositories?q=system-prompt-design+llm-instructions&sort=stars&per_page=5'"
    ["13"]="github|Multi-Agent|curl -sL 'https://api.github.com/search/repositories?q=multi-agent+orchestration&sort=stars&per_page=5'"
    ["15"]="github|PARA Zettelkasten|curl -sL 'https://api.github.com/search/repositories?q=para-method+zettelkasten-templates&sort=stars&per_page=5'"
    ["17"]="github|Dotfiles Config|curl -sL 'https://api.github.com/search/repositories?q=dotfiles-manager+templates&sort=stars&per_page=5'"
    ["19"]="github|Chinese Blogs|curl -sL 'https://api.github.com/search/repositories?q=prompt-engineering-chinese+gpt-tutorial-zh&sort=stars&per_page=5'"
    ["20"]="github|Reddit Tools|curl -sL 'https://api.github.com/search/repositories?q=reddit-chatgpt-prompts&sort=stars&per_page=5'"
    ["21"]="github|HN Tools|curl -sL 'https://api.github.com/search/repositories?q=hackernews-ai-prompts&sort=stars&per_page=5'"
    ["22"]="github|Product Hunt|curl -sL 'https://api.github.com/search/repositories?q=product-hunt-ai-tools&sort=updated&per_page=5'"
    ["23"]="github|Papers Code|curl -sL 'https://api.github.com/search/repositories?q=papers-with-code-llm-prompts&sort=stars&per_page=5'"
)

# 获取当前小时的任务
CURRENT_TASK="${SEARCH_TASKS[$HOUR]}"

if [ -z "$CURRENT_TASK" ]; then
    # 默认任务
    CURRENT_TASK="github|General Template Search|curl -sL 'https://api.github.com/search/repositories?q=agent+template+prompts&sort=updated&per_page=5'"
fi

# 解析任务
IFS='|' read -r SOURCE_TYPE NAME COMMAND <<< "$CURRENT_TASK"

echo "🔍 [$HOUR:00] 搜索源: $SOURCE_TYPE | 主题: $NAME" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 创建报告头部
cat > "$REPORT_FILE" << EOF
# Hourly Multi-Source Report

**时间**: $(date)
**小时**: $HOUR:00
**搜索源**: $SOURCE_TYPE
**主题**: $NAME

---

## 搜索结果

EOF

# 执行搜索
echo "执行: $COMMAND" | tee -a "$LOG_FILE"

if [ "$SOURCE_TYPE" = "github" ]; then
    # GitHub API 搜索
    RESPONSE=$(eval "$COMMAND" 2>/dev/null)
    
    # 解析结果
    echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data.get('items', [])
    print(f'### GitHub 发现 ({len(items)} 个仓库)\n')
    for item in items[:5]:
        stars = item['stargazers_count']
        if stars > 10000:
            icon = '🔥🔥'
        elif stars > 1000:
            icon = '🔥'
        elif stars > 100:
            icon = '⭐'
        else:
            icon = '•'
        print(f\"{icon} **{item['full_name']}**\")
        print(f\"   - ⭐ {stars} stars | 🍴 {item['forks_count']} forks\")
        print(f\"   - {item.get('description', 'No description')[:100]}\")
        print(f\"   - 🔗 {item['html_url']}\")
        print()
except:
    print('搜索出错或没有结果')
" >> "$REPORT_FILE" 2>/dev/null

elif [ "$SOURCE_TYPE" = "web" ]; then
    # 直接抓取网页
    RESULT=$(eval "$COMMAND" 2>/dev/null)
    
    echo "### Web 文档发现" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    if [ -n "$RESULT" ]; then
        echo "$RESULT" | head -15 | while read -r line; do
            if [ -n "$line" ]; then
                echo "- $line" >> "$REPORT_FILE"
            fi
        done
    else
        echo "- 无法获取内容 (可能需要特殊处理)" >> "$REPORT_FILE"
    fi
    echo "" >> "$REPORT_FILE"
fi

# 完成报告
echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "*自动生成于 $(date)*" >> "$REPORT_FILE"

# 汇总日志
echo "" | tee -a "$LOG_FILE"
echo "✅ 搜索完成" | tee -a "$LOG_FILE"
echo "📄 报告: $REPORT_FILE" | tee -a "$LOG_FILE"

# 高价值检测并标记
if [ "$SOURCE_TYPE" = "github" ]; then
    HIGH_VALUE=$(eval "$COMMAND" 2>/dev/null | grep -o '"stargazers_count":[0-9]*' | grep -o '[0-9]*' | awk '$1 > 1000 {print}' | wc -l)
    if [ "$HIGH_VALUE" -gt 0 ]; then
        echo "🔥 发现 $HIGH_VALUE 个高价值仓库 (>1000 stars)" | tee -a "$LOG_FILE"
        echo "$(date): $HOUR:00 - $NAME - $HIGH_VALUE 高价值" >> "$WORK_DIR/high_value_queue.txt"
    fi
fi
