#!/bin/bash
# MoltCare Hourly Template Mining Workflow
# 每小时执行的模板挖掘完整流程

set -e

WORKSPACE="$HOME/.openclaw/workspace/moltcare-open"
RESEARCH_DIR="$WORKSPACE/research"
LOG_DIR="$WORKSPACE/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y-%m-%d)
HOUR=$(date +%H)

# 确保目录存在
mkdir -p "$RESEARCH_DIR/hourly"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/mining_${TIMESTAMP}.log"
REPORT_FILE="$RESEARCH_DIR/hourly/mining_report_${TIMESTAMP}.md"

echo "🦞 MoltCare Hourly Template Mining" | tee -a "$LOG_FILE"
echo "=================================" | tee -a "$LOG_FILE"
echo "时间: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 1. 搜索关键词轮换
SEARCH_KEYWORDS=(
  "Anthropic prompt engineering system prompt best practices"
  "OpenAI GPT-4 system prompt examples official"
  "CrewAI agent role definition template"
  "LangChain hub prompt templates"
  "AutoGPT autonomous agent prompts"
  "LLM agent framework configuration template"
  "Claude system prompt personality definition"
  "AI agent cognitive architecture patterns"
)

# 根据小时选择关键词（每小时轮换）
KEYWORD_INDEX=$((10#$HOUR % ${#SEARCH_KEYWORDS[@]}))
SELECTED_KEYWORD="${SEARCH_KEYWORDS[$KEYWORD_INDEX]}"

echo "🔍 搜索关键词: $SELECTED_KEYWORD" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 2. 创建报告头部
cat > "$REPORT_FILE" << EOF
# Hourly Template Mining Report

**时间**: $(date)
**周期**: 第 $HOUR 小时
**关键词**: $SELECTED_KEYWORD
**状态**: 🔄 进行中

---

## 搜索执行

### 使用的关键词
\`$SELECTED_KEYWORD\`

### 搜索结果摘要
EOF

# 3. 执行搜索（使用 GitHub API 作为搜索源）
echo "📡 执行搜索..." | tee -a "$LOG_FILE"

# GitHub API 搜索（每小时限制 60 次，合理范围内）
SEARCH_QUERY=$(echo "$SELECTED_KEYWORD" | tr ' ' '+')
RESPONSE=$(curl -sL "https://api.github.com/search/repositories?q=${SEARCH_QUERY}&sort=updated&order=desc&per_page=5" 2>/dev/null || echo '{"items":[]}')

# 解析结果
REPO_COUNT=$(echo "$RESPONSE" | grep -o '"full_name"' | wc -l)
echo "发现仓库: $REPO_COUNT" | tee -a "$LOG_FILE"

# 4. 生成发现摘要
echo "" >> "$REPORT_FILE"
echo "发现 $REPO_COUNT 个相关仓库:" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ "$REPO_COUNT" -gt 0 ]; then
    echo "$RESPONSE" | grep -E '"full_name"|"html_url"|"description"' | head -30 | while read -r line; do
        echo "$line" | sed 's/^[[:space:]]*/- /' >> "$REPORT_FILE"
    done
fi

# 5. 更新累计发现日志
cat >> "$RESEARCH_DIR/hourly/discoveries_${DATE}.md" << EOF

## $(date +%H:%M) - 第 ${HOUR} 小时
- 关键词: \`$SELECTED_KEYWORD\`
- 发现: $REPO_COUNT 个仓库
- 报告: [mining_report_${TIMESTAMP}.md](./mining_report_${TIMESTAMP}.md)
EOF

# 6. 检查是否有高价值发现（需要人工审查）
echo "" | tee -a "$LOG_FILE"
echo "🔎 检查高价值发现..." | tee -a "$LOG_FILE"

# 关键词匹配高价值信号
HIGH_VALUE_PATTERNS=("anthropic" "openai" "langchain" "crewai" "autogpt" "prompt-engineering" "system-prompt")
HIGH_VALUE_COUNT=0

for pattern in "${HIGH_VALUE_PATTERNS[@]}"; do
    if echo "$RESPONSE" | grep -qi "$pattern"; then
        HIGH_VALUE_COUNT=$((HIGH_VALUE_COUNT + 1))
    fi
done

echo "高价值匹配: $HIGH_VALUE_COUNT" | tee -a "$LOG_FILE"

# 7. 更新报告状态
if [ "$HIGH_VALUE_COUNT" -gt 0 ]; then
    echo "" >> "$REPORT_FILE"
    echo "---" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "## ⚠️ 需要关注" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "发现 $HIGH_VALUE_COUNT 个高价值匹配，建议人工审查。" >> "$REPORT_FILE"
    
    # 添加到待审查队列
    echo "$(date): 关键词 '$SELECTED_KEYWORD' 发现 $HIGH_VALUE_COUNT 个高价值匹配" >> "$RESEARCH_DIR/review_queue.txt"
fi

# 8. 更新报告状态为完成
sed -i 's/🔄 进行中/✅ 完成/g' "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "*自动生成于 $(date)*" >> "$REPORT_FILE"

# 9. 清理旧日志（保留最近 7 天）
find "$LOG_DIR" -name "mining_*.log" -mtime +7 -delete 2>/dev/null || true
find "$RESEARCH_DIR/hourly" -name "mining_report_*.md" -mtime +7 -delete 2>/dev/null || true

# 10. 输出摘要
echo "" | tee -a "$LOG_FILE"
echo "✅ 每小时挖掘完成" | tee -a "$LOG_FILE"
echo "- 报告: $REPORT_FILE" | tee -a "$LOG_FILE"
echo "- 日志: $LOG_FILE" | tee -a "$LOG_FILE"
echo "- 高价值发现: $HIGH_VALUE_COUNT" | tee -a "$LOG_FILE"

# 11. 如果这是第 24 次运行（一天结束），生成日报
if [ "$HOUR" = "23" ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "📊 生成日报..." | tee -a "$LOG_FILE"
    
    DAILY_REPORT="$RESEARCH_DIR/daily_report_${DATE}.md"
    
    cat > "$DAILY_REPORT" << EOF
# Daily Template Mining Report - $DATE

## 执行统计
- 总搜索次数: 24
- 关键词覆盖: ${#SEARCH_KEYWORDS[@]} 个主题
- 总发现仓库: $(grep -c "发现:" "$RESEARCH_DIR/hourly/discoveries_${DATE}.md" 2>/dev/null || echo "0")

## 待审查队列
$(cat "$RESEARCH_DIR/review_queue.txt" 2>/dev/null | grep "^$DATE" || echo "无")

## 下一步行动
- [ ] 审查今日高价值发现
- [ ] 提取可借鉴元素
- [ ] 更新 template-discoveries.md

---
*自动生成于 $(date)*
EOF

    echo "日报已生成: $DAILY_REPORT" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "下次执行: 下个小时" | tee -a "$LOG_FILE"
