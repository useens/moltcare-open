#!/bin/bash
# Moltbook 社交自动化 - Cron 启动脚本 v8.0
# 运行频率：每15分钟

cd /root/.openclaw/workspace
export PATH="/root/.nvm/versions/node/v22.22.0/bin:$PATH"

LOG_DIR="logs"
mkdir -p $LOG_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/moltbook_social_${TIMESTAMP}.log"

echo "===========================================" >> $LOG_FILE
echo "$(date): Moltbook Social v8.0 Starting" >> $LOG_FILE
echo "===========================================" >> $LOG_FILE

# 运行主脚本
python3 scripts/moltbook_social_v8.py >> $LOG_FILE 2>&1

echo "$(date): Done" >> $LOG_FILE
echo "" >> $LOG_FILE

# 清理旧日志（保留最近20个）
ls -t $LOG_DIR/moltbook_social_*.log | tail -n +21 | xargs rm -f 2>/dev/null
