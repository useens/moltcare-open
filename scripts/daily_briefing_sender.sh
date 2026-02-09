#!/bin/bash
# Daily Briefing Sender
# Uses openclaw to send message via message tool

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
DATE=$(date '+%Y-%m-%d')
MEMORY_DIR="/root/.openclaw/workspace/memory"
WORKSPACE="/root/.openclaw/workspace"
HAS_ISSUE=0
ISSUES=()

# ==================== 系统健康检查 ====================

# 磁盘使用情况
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
DISK_INFO=$(df -h / | awk 'NR==2 {print $3"/"$2 " ("$5")"}')

# 内存使用情况
MEM_INFO=$(free -h | awk '/^Mem:/ {printf "%s/%s (%.0f%%)", $3, $2, $3/$2*100}')
MEM_PERCENT=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2*100}')

# 检查备份（检查memory目录最新文件）
BACKUP_STATUS="✓ 正常"
if [ -d "$MEMORY_DIR" ]; then
    LATEST_BACKUP=$(ls -t "$MEMORY_DIR"/*.md 2>/dev/null | head -1)
    if [ -z "$LATEST_BACKUP" ]; then
        BACKUP_STATUS="⚠ 无记录"
        HAS_ISSUE=1
        ISSUES+=("无备份记录")
    fi
else
    BACKUP_STATUS="✗ 目录不存在"
    HAS_ISSUE=1
    ISSUES+=("Memory目录不存在")
fi

# 系统健康告警判断
if [ "$DISK_USAGE" -gt 90 ]; then
    HAS_ISSUE=1
    ISSUES+=("磁盘空间严重不足: ${DISK_USAGE}%")
elif [ "$DISK_USAGE" -gt 80 ]; then
    HAS_ISSUE=1
    ISSUES+=("磁盘空间警告: ${DISK_USAGE}%")
fi

if [ "$MEM_PERCENT" -gt 90 ]; then
    HAS_ISSUE=1
    ISSUES+=("内存使用过高: ${MEM_PERCENT}%")
fi

# 检查OpenClaw Gateway状态
GATEWAY_STATUS=$(openclaw gateway status 2>/dev/null | grep -o "running\|stopped" || echo "unknown")
if [ "$GATEWAY_STATUS" != "running" ]; then
    HAS_ISSUE=1
    ISSUES+=("OpenClaw Gateway未运行")
fi

# ==================== 今日进化执行摘要 ====================
TODAY_FILE="$MEMORY_DIR/$DATE.md"
TODAY_COUNT=0
if [ -f "$TODAY_FILE" ]; then
    TODAY_COUNT=$(grep -cE "^\s*-\s*\[x\]" "$TODAY_FILE" 2>/dev/null || echo 0)
fi

# ==================== 统计项目 ====================
GIT_COMMITS=0
if [ -d "$WORKSPACE/.git" ]; then
    GIT_COMMITS=$(cd "$WORKSPACE" && git log --oneline --since="$(date '+%Y-%m-%d 00:00')" 2>/dev/null | wc -l)
fi

# ==================== 生成简报内容 ====================

if [ "$HAS_ISSUE" -eq 0 ]; then
    # 极简格式 - 无异常
    MESSAGE="📊 **每日简报** \`${DATE}\`

✅ 系统正常 | 💾 ${DISK_INFO} | 🧠 ${MEM_INFO}

📈 今日完成: ${TODAY_COUNT} 项 | 💻 提交: ${GIT_COMMITS} 次

_晚安 🌙_"
else
    # 详细格式 - 有异常
    ALERT_TEXT=$(printf "- %s\n" "${ISSUES[@]}")
    MESSAGE="📊 **每日简报** \`${DATE}\`

⚠️ **系统告警**
${ALERT_TEXT}

💻 **系统状态**
- 磁盘: \`${DISK_INFO}\`
- 内存: \`${MEM_INFO}\`
- 备份: \`${BACKUP_STATUS}\`
- Gateway: \`${GATEWAY_STATUS}\`

📈 **今日**: ${TODAY_COUNT} 项完成 | 💻 ${GIT_COMMITS} 次提交

_需要关注 ⚡_"
fi

# 使用openclaw message工具发送
echo "$MESSAGE" | openclaw message send --channel feishu --stdin

# 记录日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Daily briefing sent. Issues: $HAS_ISSUE" >> /var/log/openclaw_briefing.log
