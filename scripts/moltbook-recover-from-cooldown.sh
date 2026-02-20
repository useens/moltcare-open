#!/bin/bash
# Moltbook 账号恢复脚本
# 执行时间: 2026-02-21 21:45 (24小时后)
# 功能: 恢复 Moltbook 正常活动频率

echo "[$(date)] 恢复 Moltbook 正常活动频率" >> /root/.openclaw/workspace/logs/moltbook-recovery.log

# 恢复完整 crontab
crontab /root/.openclaw/workspace/config/unified-cron-v23.txt

echo "[$(date)] Moltbook 活动已恢复正常" >> /root/.openclaw/workspace/logs/moltbook-recovery.log

# 发送通知
echo "✅ Moltbook 24小时冷却期结束，已恢复正常活动频率"
