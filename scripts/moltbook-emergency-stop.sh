#!/bin/bash
# 停止所有 Moltbook 自动化任务
# 在检测到挑战时使用

echo "╔══════════════════════════════════════════════════════╗"
echo "║ 🛑 停止 Moltbook 自动化任务                      ║"
echo "║ 时间: $(date)                                      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# 备份当前 crontab
BACKUP_FILE="/root/.openclaw/workspace/crontab-emergency-backup-$(date +%Y%m%d_%H%M%S).txt"
crontab -l > "$BACKUP_FILE"
echo "📦 已备份到: $BACKUP_FILE"

# 移除所有 Moltbook 相关任务
echo ""
echo "🗑️  移除 Moltbook 自动化任务..."
crontab -l | grep -v "moltbook" | grep -v "Moltbook" | crontab -

# 显示剩余任务
echo ""
echo "📋 剩余的 cron 任务:"
echo "═══════════════════════════════════════════════════════"
crontab -l
echo "═══════════════════════════════════════════════════════"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║ ✅ 所有 Moltbook 自动化任务已停止                ║"
echo "║                                                      ║"
echo "║ 恢复命令:                                           ║"
echo "║   bash /root/.openclaw/workspace/scripts/apply-moltbook-safe-config.sh  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
