#!/bin/bash
# 森森·能耗模式自动切换 Cron任务
# 根据时间自动切换运行模式

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="/var/log/sensen-power-mode.log"

# 记录日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 获取当前小时
HOUR=$(date +%H)

# 时间规则
if [ "$HOUR" -ge 1 ] && [ "$HOUR" -lt 6 ]; then
    # 01:00-06:00 冻结模式
    MODE="frozen"
    REASON="深夜时段 01:00-06:00"
elif [ "$HOUR" -ge 22 ] || [ "$HOUR" -lt 7 ]; then
    # 22:00-07:00 节能模式
    MODE="eco"
    REASON="夜间时段 22:00-07:00"
else
    # 07:00-22:00 均衡模式
    MODE="balanced"
    REASON="日间时段 07:00-22:00"
fi

# 检查当前模式
CURRENT_MODE=$(cat "$WORKSPACE/memory/power-mode-state.json" 2>/dev/null | grep -o '"mode": "[^"]*"' | cut -d'"' -f4)

if [ "$CURRENT_MODE" != "$MODE" ]; then
    log "切换模式: $CURRENT_MODE → $MODE | $REASON"
    cd "$WORKSPACE" && python3 scripts/power-mode-manager.py switch "$MODE" 2>&1 | tee -a "$LOG_FILE"
    
    # 发送通知（如果配置了Feishu webhook）
    if [ -n "$FEISHU_WEBHOOK" ]; then
        curl -s -X POST "$FEISHU_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"🌲 森森自动切换至$(echo $MODE | sed 's/performance/性能模式/;s/balanced/均衡模式/;s/eco/节能模式/;s/frozen/冻结模式/')\n原因: $REASON\"}}" > /dev/null 2>&1
    fi
else
    log "保持模式: $MODE | $REASON"
fi
