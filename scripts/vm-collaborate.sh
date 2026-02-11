#!/bin/bash
# VM协作任务包装器
# 用法: vm-collaborate.sh "任务描述" "命令"

TASK_DESC="${1:-未命名任务}"
shift
COMMAND="$@"

LOG_FILE="$HOME/.openclaw/logs/vm-collaboration.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ================================" | tee -a "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] VM协作任务: $TASK_DESC" | tee -a "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ================================" | tee -a "$LOG_FILE"

# Step 1: 复活同步（必须）
echo "[*] Step 1: VM复活同步..." | tee -a "$LOG_FILE"
if ! /root/.openclaw/workspace/scripts/vm-resurrection-sync.sh >> "$LOG_FILE" 2>&1; then
    echo "[✗] VM复活失败，终止任务" | tee -a "$LOG_FILE"
    exit 1
fi

# Step 2: 执行协作任务
echo "[*] Step 2: 在VM上执行任务..." | tee -a "$LOG_FILE"
echo "    命令: $COMMAND" | tee -a "$LOG_FILE"

ssh -p 4444 -o StrictHostKeyChecking=no root@localhost "$COMMAND" 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo "[✓] VM协作任务完成: $TASK_DESC" | tee -a "$LOG_FILE"
else
    echo "[✗] VM协作任务失败 (exit $EXIT_CODE): $TASK_DESC" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
exit $EXIT_CODE
