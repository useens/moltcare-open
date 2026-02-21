#!/bin/bash
# 应用 Moltbook 安全频率配置
# 版本: 2026-02-21

WORKSPACE="/root/.openclaw/workspace"
CONFIG_FILE="$WORKSPACE/config/moltbook-cron-safe.txt"

echo "╔══════════════════════════════════════════════════════╗"
echo "║ 🛡️ 应用 Moltbook 安全频率配置                      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# 备份当前 crontab
echo "📦 [1/4] 备份当前 crontab..."
crontab -l > "$WORKSPACE/crontab-backup-$(date +%Y%m%d_%H%M%S).txt"
echo "   ✅ 备份完成"

# 移除旧的 Moltbook cron 任务
echo ""
echo "🗑️  [2/4] 移除旧的 Moltbook 任务..."
crontab -l | grep -v "moltbook" | crontab -
echo "   ✅ 旧任务已移除"

# 添加新的安全配置
echo ""
echo "➕ [3/4] 添加新的安全频率配置..."
crontab -l | cat - "$CONFIG_FILE" | crontab -
echo "   ✅ 安全配置已添加"

# 显示新配置
echo ""
echo "📋 [4/4] 新的 Moltbook 任务："
echo "═══════════════════════════════════════════════════════"
crontab -l | grep -i moltbook
echo "═══════════════════════════════════════════════════════"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║ ✅ 安全频率配置已应用                             ║"
echo "║                                                      ║"
echo "║ 频率调整：                                          ║"
echo "║   • 互动：每小时 → 每2小时                          ║"
echo "║   • 检查：每30分钟 → 每4小时                        ║"
echo "║   • 学习：每天 → 每3天                              ║"
echo "║                                                      ║"
echo "║ 解封恢复：2026-02-21 22:30                         ║"
echo "║ 状态检查：每天 22:05                                ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
