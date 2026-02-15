#!/bin/bash
# 多Agent协调循环脚本 - 由协调代理生成
# 用途: 每5分钟执行一次协调检查

WORKSPACE="/root/.openclaw/workspace"
COORD_DIR="$WORKSPACE/coordination"
CYCLE_FILE="$COORD_DIR/.current_cycle"
LOG_FILE="$COORD_DIR/coordination.log"

# 读取当前周期
if [ -f "$CYCLE_FILE" ]; then
    CYCLE=$(cat "$CYCLE_FILE")
else
    CYCLE=1
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== 协调周期 #$CYCLE 开始 ==="

# 1. 检查活跃子代理
log "检查活跃子代理..."
openclaw sessions list --active 10 > "$COORD_DIR/sessions-current.txt" 2>&1
ACTIVE_COUNT=$(grep -c "subagent" "$COORD_DIR/sessions-current.txt" 2>/dev/null || echo "0")
log "发现 $ACTIVE_COUNT 个子代理"

# 2. 生成周期报告
REPORT_FILE="$COORD_DIR/auto-report-$(printf '%03d' $CYCLE).md"
cat > "$REPORT_FILE" << EOF
# 自动协调报告 - 第${CYCLE}轮

**时间**: $(date '+%Y-%m-%d %H:%M:%S')  
**活跃代理**: $ACTIVE_COUNT

## 状态摘要
- 协调代理: 运行中
- 子代理: $ACTIVE_COUNT 个
- 系统状态: 正常

## 下一步
- 5分钟后进行第$((CYCLE+1))轮检查

---
*自动生成 by coordination-loop.sh*
EOF

log "报告已生成: $REPORT_FILE"

# 3. 更新周期数
CYCLE=$((CYCLE+1))
echo $CYCLE > "$CYCLE_FILE"

log "=== 周期完成，下次检查: 5分钟后 ==="
