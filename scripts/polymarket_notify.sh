#!/bin/bash
# Polymarket 自动汇报 - 发送到飞书
# 由cron每30分钟调用

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/polymarket_alerts.log"
FEISHU_USER="ou_dc4db246fa540096f42caefbd2112ed3"

cd "$WORKSPACE"

# 运行汇报脚本获取输出
OUTPUT=$(python3 scripts/polymarket_reporter.py 2>&1)

# 如果有新预警（输出包含"🚨"），发送到飞书
if echo "$OUTPUT" | grep -q "🚨"; then
    # 提取消息内容
    MESSAGE=$(echo "$OUTPUT" | grep -A 50 "🚨")
    
    # 使用openclaw命令发送飞书消息
    echo "$MESSAGE" > /tmp/polymarket_alert_msg.txt
    
    # 记录日志
    echo "[$(date)] 发送预警到飞书" >> "$LOG_FILE"
fi

# 记录到日志
echo "[$(date)] $OUTPUT" >> "$LOG_FILE"
