#!/bin/bash
# MoltCare Hourly Template Mining - 智能关键词轮换

HOUR=$(date +%H)

# 24个高质量关键词 - 每小时一个
KEYWORDS=(
  # 官方资源 (高优先级)
  "anthropics/prompt-eng-interactive-tutorial"
  "openai/openai-cookbook examples prompts"
  "microsoft/promptflow examples"
  "langchain-ai/langchain-hub"
  
  # 系统提示合集 (高质量)
  "system-prompts-leaks"
  "leaked-system-prompts"
  "TheBigPromptLibrary"
  "awesome-system-prompts"
  
  # 提示工程资源
  "awesome-chatgpt-prompts"
  "prompt-engineering-guide"
  "prompt-blueprint"
  "prompt-engineering-techniques"
  
  # Agent 框架
  "crewai-examples"
  "autogpt core prompts"
  "agency-agents"
  "multi-agent-framework"
  
  # 模板/脚手架
  "obsidian-templates zettelkasten"
  "para-method templates"
  "second-brain templates"
  "devcontainer templates"
  
  # 生产力/工作流
  "llm-workflow-templates"
  "ai-automation-templates"
  "productivity-templates markdown"
  "knowledge-management templates"
)

INDEX=$((10#$HOUR))
KEYWORD="${KEYWORDS[$INDEX]}"

echo "🔍 当前关键词 [$HOUR:00]: $KEYWORD"
echo ""

# 执行搜索
curl -sL "https://api.github.com/search/repositories?q=$(echo $KEYWORD | tr ' ' '+')&sort=stars&order=desc&per_page=5" 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('items', [])
if items:
    print(f'发现 {len(items)} 个仓库:')
    print()
    for item in items[:3]:
        stars = item['stargazers_count']
        if stars > 1000:
            priority = '🔥'
        elif stars > 100:
            priority = '⭐'
        else:
            priority = '•'
        print(f\"{priority} {item['full_name']}\")
        print(f\"   ⭐ {stars} | {item.get('description', 'No desc')[:80]}\")
        print()
else:
    print('暂无新发现')
" 2>/dev/null
