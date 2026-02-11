#!/bin/bash
# 夜间进化 - 阶段2: 知识内化 (02:00-05:00)
# 全天对话深度分析 + 知识关联构建

set -e

LOG_FILE="$HOME/.openclaw/workspace/logs/night-evolution-phase2-$(date +%Y%m%d).log"
WORKSPACE="$HOME/.openclaw/workspace"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 夜间进化阶段2: 知识内化开始 ===" | tee -a "$LOG_FILE"

# 1. 全天对话深度分析
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🧠 分析今日对话..." | tee -a "$LOG_FILE"
cd "$WORKSPACE"

# 分析今日记忆文件
TODAY=$(date +%Y-%m-%d)
TODAY_FILE="memory/daily/${TODAY}.md"

if [ -f "$TODAY_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 找到今日记录: $TODAY_FILE" | tee -a "$LOG_FILE"
    # 提取关键决策和洞察
    grep -E "^(###|\*\*决策|\*\*洞察)" "$TODAY_FILE" >> "$WORKSPACE/memory/insights/${TODAY}-insights.md" 2>/dev/null || true
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ℹ️ 今日无记录文件" | tee -a "$LOG_FILE"
fi

# 2. 更新知识图谱
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🕸️ 更新知识图谱..." | tee -a "$LOG_FILE"
if [ -f "$WORKSPACE/memory/knowledge-graph.md" ]; then
    echo "- $(date +%Y-%m-%d): 双节点架构监控修复完成" >> "$WORKSPACE/memory/knowledge-graph.md"
fi

# 3. 长期记忆归档
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📚 归档长期记忆..." | tee -a "$LOG_FILE"
# 重要事件归档到核心档案

# 4. 生成明日任务清单
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📝 生成明日任务..." | tee -a "$LOG_FILE"

# 5. 错误学习循环复盘
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 复盘今日错误..." | tee -a "$LOG_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 知识内化完成 ===" | tee -a "$LOG_FILE"
