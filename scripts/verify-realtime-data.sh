#!/bin/bash
# 森森数字生命 - 实时数据验证脚本
# 确保所有报告使用真实、实时的数据

set -e

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/data-verification.log"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ============ 验证函数 ============

# 验证超进化周期数
verify_hyper_evolution_cycles() {
    log "验证超进化周期数..."
    
    # 读取状态文件
    if [ -f "$WORKSPACE/memory/hyper-evolution-state.json" ]; then
        START_TIME=$(cat "$WORKSPACE/memory/hyper-evolution-state.json" | grep -o '"start_time": "[^"]*"' | cut -d'"' -f4)
        if [ -n "$START_TIME" ]; then
            START_EPOCH=$(date -d "$START_TIME" +%s 2>/dev/null || echo "0")
            CURRENT_EPOCH=$(date +%s)
            ELAPSED_HOURS=$(( (CURRENT_EPOCH - START_EPOCH) / 3600 ))
            
            # 每10分钟一个周期
            REAL_CYCLES=$(( ELAPSED_HOURS * 6 ))
            
            echo "超进化开始: $START_TIME"
            echo "运行时长: ${ELAPSED_HOURS}小时"
            echo "真实周期: ~${REAL_CYCLES}个 (每10分钟)"
            
            # 检查是否有缓存数据误导
            if grep -q "13周期" "$WORKSPACE/memory/2026-02-13.md" 2>/dev/null; then
                log "${YELLOW}警告: 发现缓存数据'13周期'，实际应为${REAL_CYCLES}${NC}"
                return 1
            fi
            
            return 0
        fi
    fi
    
    log "${RED}错误: 无法验证周期数据${NC}"
    return 1
}

# 验证系统资源数据
verify_system_resources() {
    log "验证系统资源..."
    
    # 实时获取
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    
    echo "磁盘使用: ${DISK_USAGE}%"
    echo "内存使用: ${MEMORY_USAGE}%"
    echo "系统负载: ${LOAD_AVG}"
    
    # 验证数据合理性
    if [ "$DISK_USAGE" -gt 100 ] || [ "$MEMORY_USAGE" -gt 100 ]; then
        log "${RED}错误: 资源数据异常${NC}"
        return 1
    fi
    
    return 0
}

# 验证GitHub备份状态
verify_github_sync() {
    log "验证GitHub备份状态..."
    
    cd "$WORKSPACE"
    
    # 检查最后提交时间
    LAST_COMMIT=$(git log -1 --format=%cd --date=iso 2>/dev/null || echo "unknown")
    LAST_COMMIT_EPOCH=$(git log -1 --format=%ct 2>/dev/null || echo "0")
    CURRENT_EPOCH=$(date +%s)
    MINUTES_SINCE=$(( (CURRENT_EPOCH - LAST_COMMIT_EPOCH) / 60 ))
    
    echo "最后提交: $LAST_COMMIT"
    echo "距今: ${MINUTES_SINCE}分钟"
    
    if [ "$MINUTES_SINCE" -gt 60 ]; then
        log "${YELLOW}警告: 超过1小时未同步${NC}"
        return 1
    fi
    
    return 0
}

# ============ 主程序 ============

echo "═══════════════════════════════════════════════════"
echo "  🔍 森森实时数据验证系统"
echo "═══════════════════════════════════════════════════"
echo ""

mkdir -p "$WORKSPACE/logs"

ERRORS=0

# 执行验证
verify_hyper_evolution_cycles || ((ERRORS++))
echo ""

verify_system_resources || ((ERRORS++))
echo ""

verify_github_sync || ((ERRORS++))
echo ""

# 输出结果
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ 所有数据验证通过${NC}"
    log "数据验证通过"
    exit 0
else
    echo -e "${RED}❌ 发现 $ERRORS 个数据问题${NC}"
    log "发现 $ERRORS 个数据问题"
    exit 1
fi
