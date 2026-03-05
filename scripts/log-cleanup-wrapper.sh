#!/bin/bash
# 日志清理包装器 - 由NB05执行
NODE="NB05"
LOG_FILE="/root/.openclaw/workspace/nanobots/nb05/logs/cleanup.log"

echo "[$NODE] $(date) 开始日志清理" >> "$LOG_FILE"

# 清理旧日志
find /root/.openclaw/workspace/logs -name "*.log" -mtime +7 -delete 2>/dev/null
find /root/.openclaw/workspace/nanobots/*/logs -name "*.log" -mtime +3 -delete 2>/dev/null

# 清理旧快照
find /root/.openclaw/workspace/.snapshots -name "snapshot_*.tar.gz" -mtime +7 -delete 2>/dev/null

echo "[$NODE] $(date) 日志清理完成" >> "$LOG_FILE"
