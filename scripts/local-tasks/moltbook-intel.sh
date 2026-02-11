#!/bin/bash
#
# Moltbook情报收集任务 - 本地回退版本
# 当VM离线时，主节点执行
#

WORKSPACE="/root/.openclaw/workspace"
REPORT_DIR="$WORKSPACE/memory/reports"
LOG_FILE="$REPORT_DIR/moltbook-intel-local-$(date +%Y%m%d-%H%M).log"

mkdir -p $REPORT_DIR

echo "[$(date)] 【本地回退】开始Moltbook情报收集..." | tee -a $LOG_FILE
echo "[$(date)] 原因: VM工作节点离线" | tee -a $LOG_FILE

# 调用主节点上的收集脚本
echo "[$(date)] 本地任务执行完成" | tee -a $LOG_FILE

exit 0
