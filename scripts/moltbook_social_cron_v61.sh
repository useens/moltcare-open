#!/bin/bash
# Moltbook 社交自动化 v6.1 - Cron 执行脚本
# 分两步执行：扫描 -> 生成和发送

cd /root/.openclaw/workspace
export PATH="/root/.nvm/versions/node/v22.22.0/bin:$PATH"

LOG_FILE="logs/moltbook_social_v61.log"

mkdir -p logs
echo "========================================" >> $LOG_FILE
echo "$(date): Starting Moltbook Social v6.1" >> $LOG_FILE
echo "========================================" >> $LOG_FILE

# 第一步：扫描任务
echo "Step 1: Scanning..." >> $LOG_FILE
python3 scripts/moltbook_social_v61.py >> $LOG_FILE 2>&1

# 检查是否有待处理任务
if [ -f /tmp/moltbook_pending_v61.json ]; then
    echo "Step 2: Generating and sending replies..." >> $LOG_FILE
    
    # 注意：generate脚本需要在OpenClaw环境中运行
    # 这里我们创建一个标记文件，主会话会处理它
    touch /tmp/moltbook_needs_processing
    echo "   Marked for processing by main session" >> $LOG_FILE
else
    echo "No pending tasks" >> $LOG_FILE
fi

echo "$(date): Done" >> $LOG_FILE
echo "" >> $LOG_FILE
