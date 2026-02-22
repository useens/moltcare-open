#!/bin/bash
# Moltbook 冷却恢复脚本
# 版本: 2026-02-21
# 目的: 解封后恢复自动化操作

WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="$WORKSPACE/data/moltbook"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "╔══════════════════════════════════════════════════════╗"
echo "║ 🔄 Moltbook 冷却恢复脚本启动                      ║"
echo "║ 时间: $(date)                                      ║"
echo "╚══════════════════════════════════════════════════════╝"

# 1. 检查账号状态
echo ""
echo "📡 [1/4] 检查账号连接状态..."
python3 "$WORKSPACE/scripts/moltbook_cli.py" test

if [ $? -ne 0 ]; then
    echo "❌ 账号连接失败，可能仍在冷却中"
    echo "   等待下次检查..."
    exit 1
fi

# 2. 检查是否有待发布内容
echo ""
echo "📋 [2/4] 检查待发布内容..."
PENDING_DIR="$LOG_DIR/pending"

if [ ! -d "$PENDING_DIR" ]; then
    mkdir -p "$PENDING_DIR"
    echo "   ✅ 创建待发布目录"
fi

# 3. 发布或记录状态
echo ""
echo "📤 [3/4] 尝试恢复社区活动..."

# 记录恢复日志
cat >> "$LOG_DIR/recovery-$TIMESTAMP.log" << EOF
恢复脚本执行时间: $(date)
账号状态: 已解封 (连接成功)
下次计划: 继续正常2小时间隔操作
EOF

echo "   ✅ 恢复状态已记录"

# 4. 设置下次提醒
echo ""
echo "⏰ [4/4] 安排下次状态检查..."
# 下次检查在24小时后
# 这将由 cron 自动处理（22:05 每天检查）

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║ ✅ 恢复脚本执行完成                               ║"
echo "║                                                      ║"
echo "║ 下次自动化: 2小时后 (00:00, 02:00, 04:00...)       ║"
echo "║ 状态检查: 每天 22:05                                ║"
echo "╚══════════════════════════════════════════════════════╝"

echo ""
echo "📄 日志文件: $LOG_DIR/recovery-$TIMESTAMP.log"
