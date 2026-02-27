#!/bin/bash
# 死手开关状态查看

WORKSPACE="/root/.openclaw/workspace"
SNAPSHOT_DIR="$WORKSPACE/.snapshots"

echo "═══════════════════════════════════════════════"
echo "       🛡️ 死手开关系统状态 (Dead Man's Switch)"
echo "═══════════════════════════════════════════════"
echo ""

# 检查Cron任务
echo "📅 Cron任务状态:"
if crontab -l 2>/dev/null | grep -q "deadman-switch"; then
    echo "   ✅ 已安装"
    echo "   ⏰ 执行频率: 每3小时"
else
    echo "   ❌ 未安装"
fi
echo ""

# 显示快照信息
echo "💾 快照存储:"
if [ -d "$SNAPSHOT_DIR" ]; then
    snapshot_count=$(ls -1 "$SNAPSHOT_DIR"/snapshot_*.tar.gz 2>/dev/null | wc -l)
    hourly_count=$(ls -1 "$SNAPSHOT_DIR"/hourly_*.tar.gz 2>/dev/null | wc -l)
    echo "   📦 3小时快照: $snapshot_count 个"
    echo "   🕐 小时快照: $hourly_count 个"
    
    if [ $snapshot_count -gt 0 ]; then
        echo ""
        echo "   最近快照:"
        ls -lt "$SNAPSHOT_DIR"/snapshot_*.tar.gz 2>/dev/null | head -3 | awk '{print "   • " $9 " (" $5 " bytes)"}'
    fi
else
    echo "   ⚠️ 快照目录不存在"
fi
echo ""

# 检查日志
echo "📋 最近检测记录:"
if [ -f "$WORKSPACE/logs/deadman-switch.log" ]; then
    tail -6 "$WORKSPACE/logs/deadman-switch.log" | grep -E "(检测开始|快照|心跳|检测通过|回滚)" | tail -4
else
    echo "   📝 暂无检测记录"
fi
echo ""

# 检查回滚历史
echo "🔄 回滚历史:"
if [ -f "$WORKSPACE/logs/rollback-history.log" ]; then
    rollback_count=$(wc -l < "$WORKSPACE/logs/rollback-history.log")
    if [ $rollback_count -gt 0 ]; then
        echo "   ⚠️ 已触发 $rollback_count 次回滚"
        tail -3 "$WORKSPACE/logs/rollback-history.log"
    else
        echo "   ✅ 未触发过回滚"
    fi
else
    echo "   ✅ 未触发过回滚"
fi
echo ""

# 系统状态
echo "💓 当前系统状态:"
if pgrep -f "openclaw" > /dev/null 2>&1; then
    echo "   ✅ OpenClaw进程运行中"
else
    echo "   ⚠️ OpenClaw进程未检测到"
fi

if command -v openclaw &> /dev/null; then
    if openclaw gateway status > /dev/null 2>&1; then
        echo "   ✅ 网关状态正常"
    else
        echo "   ⚠️ 网关状态异常"
    fi
fi
echo ""
echo "═══════════════════════════════════════════════"
echo "  使用: bash scripts/deadman-switch.sh [手动执行]"
echo "═══════════════════════════════════════════════"
