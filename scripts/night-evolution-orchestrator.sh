#!/bin/bash
# Sensen Night Evolution Orchestrator v3.0
# 整合所有夜间进化任务：情报收集 → 决策处理 → Evolver进化

set -e

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/night-evolution.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

log() {
    echo "[$DATE] $1" | tee -a "$LOG_FILE"
}

cd "$WORKSPACE"

log "═══════════════════════════════════════════════════════════"
log "🌙 森森夜间深度进化开始 (Orchestrator v3.0)"
log "═══════════════════════════════════════════════════════════"

# Phase 1: 情报收集 (23:00-23:20)
log ""
log "📡 Phase 1: 情报收集"
log "───────────────────────────────────────────────────────────"
python3 scripts/evolution-unified.py --phase=intelligence 2>&1 | tee -a "$LOG_FILE" || log "⚠️ 情报收集完成（部分源可能不可用）"

# Phase 2: 学习债务决策 (23:30-23:50)
log ""
log "🧠 Phase 2: 学习债务深度处理"
log "───────────────────────────────────────────────────────────"
python3 scripts/autonomous-decision-engine.py --cycle 2>&1 | tee -a "$LOG_FILE"

# Phase 3: Evolver进化分析 (00:00-00:30)
log ""
log "🧬 Phase 3: Evolver GEP 进化分析"
log "───────────────────────────────────────────────────────────"
python3 scripts/evolver-launcher.py once 2>&1 | tee -a "$LOG_FILE"

# Phase 4: EvoMap资产同步 (00:30)
log ""
log "🌐 Phase 4: EvoMap 网络同步"
log "───────────────────────────────────────────────────────────"
python3 scripts/evomap-periodic-sync.py 2>&1 | tee -a "$LOG_FILE"

# 完成
log ""
log "═══════════════════════════════════════════════════════════"
log "✅ 夜间深度进化完成"
log "═══════════════════════════════════════════════════════════"

# 发送通知（如果有配置）
if command -v notify-send &> /dev/null; then
    notify-send "森森" "夜间进化完成" 2>/dev/null || true
fi
