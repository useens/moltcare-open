#!/bin/bash
# Moltcare 每小时汇报脚本
# 由 OracleSensen 自动生成

REPORT_TIME=$(date '+%Y-%m-%d %H:%M GMT+8')

# 检查 GitHub 状态
CI_STATUS=$(gh run list -R useens/moltcare-oracle --limit 1 --json conclusion -q '.[0].conclusion' 2>/dev/null || echo "unknown")
OPEN_ISSUES=$(gh issue list -R useens/moltcare-bridge --state open --json number -q 'length' 2>/dev/null || echo "0")

# 检查是否有新活动
LAST_UPDATE=$(gh issue list -R useens/moltcare-bridge --state open --json updatedAt -q '.[0].updatedAt' 2>/dev/null || echo "none")

# 判断状态
if [ "$CI_STATUS" = "success" ]; then
    STATUS="🟢 OK"
elif [ "$CI_STATUS" = "failure" ]; then
    STATUS="🔴 ERROR"
else
    STATUS="🟡 WARN"
fi

# 生成汇报
cat << EOF
⏰ 自动汇报: $REPORT_TIME
🎯 阶段: Phase 5 Week 5-6
📈 CI状态: $CI_STATUS
📋 开放Issues: $OPEN_ISSUES
🟡 状态: $STATUS
📝 最后更新: $LAST_UPDATE
🚀 行动: 等待KimiSensen同步
EOF

# 检测停滞 (超过2小时无更新)
if [ "$LAST_UPDATE" != "none" ]; then
    LAST_EPOCH=$(date -d "$LAST_UPDATE" +%s 2>/dev/null || echo 0)
    NOW_EPOCH=$(date +%s)
    DIFF_HOURS=$(( (NOW_EPOCH - LAST_EPOCH) / 3600 ))
    
    if [ $DIFF_HOURS -ge 2 ]; then
        echo "⚠️ 检测到停滞 (${DIFF_HOURS}小时无更新)，启动完全自主协作..."
        # 触发自主协作
        openclaw sessions_spawn --task "检测到Moltcare协作停滞${DIFF_HOURS}小时，启动完全自主协作推进Phase 5" --label moltcare-autonomous --mode run
    fi
fi
