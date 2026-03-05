#!/bin/bash
# Polymarket监控包装器 - 由NB04执行
NODE="NB04"
LOG_FILE="/root/.openclaw/workspace/nanobots/nb04/logs/polymarket.log"

echo "[$NODE] $(date) 开始Polymarket监控" >> "$LOG_FILE"
cd /root/.openclaw/workspace
python3 scripts/polymarket_monitor.py >> "$LOG_FILE" 2>&1

# 检查异常，如果有则通知指挥中心
if grep -q "error\|exception\|timeout" "$LOG_FILE" | tail -5; then
    echo "[$NODE] $(date) 发现异常，通知指挥中心" >> "$LOG_FILE"
    python3 scripts/feishu-sync.py high "polymarket.monitor" "NB04检测到Polymarket异常" 2>/dev/null
fi
