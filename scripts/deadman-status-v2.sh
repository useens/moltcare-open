#!/bin/bash
# 死手开关状态查看 v2.0

WORKSPACE="/root/.openclaw/workspace"
SNAPSHOT_DIR="$WORKSPACE/.snapshots"

echo "═══════════════════════════════════════════════════════"
echo "       🛡️ 死手开关系统 v2.0 状态面板"
echo "═══════════════════════════════════════════════════════"
echo ""

echo "📦 系统版本: v2.0 (增强版)"
echo "   特性: 增量备份 | 深度检测 | 智能通知 | 回滚验证"
echo ""

echo "📅 定时任务:"
if crontab -l 2>/dev/null | grep -q "deadman-switch-v2"; then
    echo "   ✅ v2.0 已安装"
    echo "   ⏰ 执行频率: 每3小时"
else
    echo "   ❌ 未安装"
fi
echo ""

echo "💾 快照存储:"
SNAPSHOT_COUNT=$(ls -1 "$SNAPSHOT_DIR"/snapshot_*.tar.gz 2>/dev/null | wc -l)
CORRUPTED_COUNT=$(ls -1 "$SNAPSHOT_DIR"/corrupted_*.tar.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sm "$SNAPSHOT_DIR" 2>/dev/null | cut -f1)
echo "   📦 正常快照: $SNAPSHOT_COUNT 个"
echo "   💥 损坏备份: $CORRUPTED_COUNT 个" 
echo "   💽 总占用: ${TOTAL_SIZE}MB"

if [ "$SNAPSHOT_COUNT" -gt 0 ]; then
    echo ""
    echo "   最近快照:"
    ls -lt "$SNAPSHOT_DIR"/snapshot_*.tar.gz 2>/dev/null | head -3 | while read -r line; do
        SIZE=$(echo "$line" | awk '{print $5}')
        NAME=$(echo "$line" | awk '{print $9}' | xargs basename)
        HSIZE=$(numfmt --to=iec "$SIZE" 2>/dev/null || echo "${SIZE}b")
        echo "   • $NAME ($HSIZE)"
    done
fi
echo ""

echo "📊 健康状态:"
if [ -f "$SNAPSHOT_DIR/health-score.json" ]; then
    SCORE=$(grep '"score"' "$SNAPSHOT_DIR/health-score.json" 2>/dev/null | grep -o '[0-9]\+')
    STATUS=$(grep '"status"' "$SNAPSHOT_DIR/health-score.json" 2>/dev/null | cut -d'"' -f4)
    TIME=$(grep '"timestamp"' "$SNAPSHOT_DIR/health-score.json" 2>/dev/null | cut -d'"' -f4)
    
    if [ -n "$SCORE" ] && [ "$SCORE" -ge 80 ]; then
        echo "   ✅ 健康评分: $SCORE/100 🟢"
    elif [ -n "$SCORE" ] && [ "$SCORE" -ge 60 ]; then
        echo "   ⚠️ 健康评分: $SCORE/100 🟡"
    else
        echo "   ❌ 健康评分: ${SCORE:-N/A}/100 🔴"
    fi
    echo "   状态: $STATUS | 检测时间: $TIME"
else
    echo "   📝 暂无健康评分记录"
fi
echo ""

echo "🔄 回滚历史:"
if [ -f "$WORKSPACE/logs/rollback-history.log" ]; then
    ROLLBACK_COUNT=$(grep -c "回滚执行" "$WORKSPACE/logs/rollback-history.log" 2>/dev/null || echo 0)
    if [ "$ROLLBACK_COUNT" -gt 0 ]; then
        echo "   ⚠️ 已触发 $ROLLBACK_COUNT 次回滚"
    else
        echo "   ✅ 未触发过回滚（运行正常）"
    fi
else
    echo "   ✅ 未触发过回滚"
fi
echo ""

echo "🧠 记忆系统:"
if [ -d "$WORKSPACE/memory" ]; then
    MEM_SIZE=$(du -sh "$WORKSPACE/memory" 2>/dev/null | cut -f1)
    VECTOR_COUNT=$(find "$WORKSPACE/memory/vector" -type f 2>/dev/null | wc -l)
    echo "   💾 占用: $MEM_SIZE"
    echo "   📁 向量文件: $VECTOR_COUNT 个"
else
    echo "   ❌ 记忆目录不存在"
fi
echo ""

echo "📢 通知队列:"
if [ -f "$WORKSPACE/.state/notifications.jsonl" ]; then
    NOTIF_COUNT=$(wc -l < "$WORKSPACE/.state/notifications.jsonl" 2>/dev/null)
    HIGH_COUNT=$(grep -c '"priority": "high"' "$WORKSPACE/.state/notifications.jsonl" 2>/dev/null || echo 0)
    CRIT_COUNT=$(grep -c '"priority": "critical"' "$WORKSPACE/.state/notifications.jsonl" 2>/dev/null || echo 0)
    echo "   总通知: $NOTIF_COUNT"
    echo "   高优先级: $HIGH_COUNT | 紧急: $CRIT_COUNT"
else
    echo "   暂无通知"
fi
echo ""

echo "💓 实时状态:"
PROC_COUNT=$(pgrep -f "openclaw" 2>/dev/null | wc -l)
if [ "$PROC_COUNT" -gt 0 ]; then
    echo "   ✅ OpenClaw进程: $PROC_COUNT 个运行中"
else
    echo "   ❌ OpenClaw进程: 未检测到"
fi

if timeout 5 openclaw gateway status > /dev/null 2>&1; then
    echo "   ✅ 网关状态: 响应正常"
else
    echo "   ⚠️ 网关状态: 无响应"
fi
echo ""

echo "═══════════════════════════════════════════════════════"
echo "  快速命令:"
echo "  • 查看状态: bash scripts/deadman-status-v2.sh"
echo "  • 手动检测: bash scripts/deadman-switch-v2.sh"
echo "  • 查看日志: tail -f logs/deadman-switch.log"
echo "═══════════════════════════════════════════════════════"
