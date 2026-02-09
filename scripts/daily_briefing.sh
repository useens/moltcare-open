#!/bin/bash
# Daily Briefing Script
# Runs at 23:50 daily

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
DATE=$(date '+%Y-%m-%d')
MEMORY_DIR="/root/.openclaw/workspace/memory"
HAS_ISSUE=0

# ==================== 系统健康检查 ====================

# 磁盘使用情况
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
DISK_INFO=$(df -h / | awk 'NR==2 {print $3"/"$2 " ("$5")"}')

# 内存使用情况
MEM_INFO=$(free -h | awk '/^Mem:/ {printf "%s/%s (%s)", $3, $2, $3/$2*100}')
MEM_PERCENT=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2*100}')

# 检查备份（检查memory目录最新文件）
if [ -d "$MEMORY_DIR" ]; then
    LATEST_BACKUP=$(ls -t "$MEMORY_DIR"/*.md 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_STATUS="✓ 正常 ($(basename "$LATEST_BACKUP"))"
    else
        BACKUP_STATUS="⚠ 无备份记录"
        HAS_ISSUE=1
    fi
else
    BACKUP_STATUS="✗ 目录不存在"
    HAS_ISSUE=1
fi

# 系统健康告警判断
HEALTH_ALERT=""
if [ "$DISK_USAGE" -gt 90 ]; then
    HEALTH_ALERT="🚨 磁盘空间不足: ${DISK_USAGE}%"
    HAS_ISSUE=1
elif [ "$DISK_USAGE" -gt 80 ]; then
    HEALTH_ALERT="⚠️ 磁盘空间警告: ${DISK_USAGE}%"
    HAS_ISSUE=1
fi

if [ "$MEM_PERCENT" -gt 90 ]; then
    HEALTH_ALERT="${HEALTH_ALERT} 🚨 内存使用过高: ${MEM_PERCENT}%"
    HAS_ISSUE=1
fi

# ==================== 今日进化执行摘要 ====================
TODAY_FILE="$MEMORY_DIR/$DATE.md"
TODAY_SUMMARY=""
if [ -f "$TODAY_FILE" ]; then
    # 提取今日完成的任务
    COMPLETED=$(grep -E "^\s*-\s*\[x\]|完成|done" "$TODAY_FILE" 2>/dev/null | head -5)
    if [ -n "$COMPLETED" ]; then
        TODAY_SUMMARY="$(echo "$COMPLETED" | head -3)"
    else
        TODAY_SUMMARY="暂无完成的任务记录"
    fi
else
    TODAY_SUMMARY="今日无记录"
fi

# ==================== 明日计划预览 ====================
TOMORROW_DATE=$(date -d "+1 day" '+%Y-%m-%d')
TOMORROW_FILE="$MEMORY_DIR/$TOMORROW_DATE.md"
TOMORROW_PLAN=""
if [ -f "$TOMORROW_FILE" ]; then
    PLANS=$(grep -E "^\s*-\s*|计划|todo|TODO" "$TOMORROW_FILE" 2>/dev/null | head -5)
    if [ -n "$PLANS" ]; then
        TOMORROW_PLAN="$(echo "$PLANS" | head -3)"
    else
        TOMORROW_PLAN="暂无明日计划"
    fi
else
    TOMORROW_PLAN="明日暂无计划文件"
fi

# ==================== 生成简报内容 ====================

# 静默模式：无异常则极简格式
if [ "$HAS_ISSUE" -eq 0 ]; then
    # 极简格式
    MESSAGE="📊 **每日简报** | \`${TIMESTAMP}\`

✅ **系统正常** | 磁盘: \`${DISK_INFO}\` | 内存: \`${MEM_INFO}\`

📈 **今日**: $TODAY_SUMMARY

📋 **明日**: $TOMORROW_PLAN"
else
    # 详细格式（有异常）
    MESSAGE="📊 **每日简报** | \`${TIMESTAMP}\`

⚠️ **系统告警**
${HEALTH_ALERT}

💻 **系统健康**
- 磁盘使用: \`${DISK_INFO}\`
- 内存使用: \`${MEM_INFO}\`
- 备份状态: \`${BACKUP_STATUS}\`

📈 **今日执行摘要**
\`\`\`
${TODAY_SUMMARY}
\`\`\`

📋 **明日计划预览**
\`\`\`
${TOMORROW_PLAN}
\`\`\`"
fi

# 发送到主渠道 (Feishu)
# 使用message工具需要openclaw环境，这里输出到日志供cron处理
echo "$MESSAGE" > /tmp/daily_briefing_msg.txt

# 尝试使用openclaw发送
if command -v openclaw &> /dev/null; then
    # 获取默认feishu channel
    openclaw message send --message-file /tmp/daily_briefing_msg.txt --channel feishu 2>/dev/null || \
    echo "Briefing generated at $TIMESTAMP" >> /var/log/daily_briefing.log
else
    echo "[$(date)] Daily Briefing:"
    cat /tmp/daily_briefing_msg.txt
fi
