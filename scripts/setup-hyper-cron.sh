#!/bin/bash
# 设置超进化模式的 cron 任务
# Setup Hyper-Evolution Cron Jobs

CRON_FILE="/tmp/hyper-evolution-cron"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"

# 清理现有超进化相关任务
crontab -l 2>/dev/null | grep -v "hyper-evolution" > "$CRON_FILE" || true

echo "# 超进化模式定时任务" >> "$CRON_FILE"
echo "# 每30分钟执行一次深度学习循环" >> "$CRON_FILE"
echo "*/30 * * * * cd $WORKSPACE_DIR && bash $SCRIPT_DIR/hyper-evolution-loop.sh >> $WORKSPACE_DIR/memory/logs/cron.log 2>&1" >> "$CRON_FILE"

# 安装新cron任务
crontab "$CRON_FILE"
rm "$CRON_FILE"

echo "✅ 超进化模式 cron 任务已设置"
echo "   执行频率: 每30分钟"
echo "   日志位置: $WORKSPACE_DIR/memory/logs/cron.log"
