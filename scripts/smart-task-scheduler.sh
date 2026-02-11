#!/bin/bash
# =============================================================================
# 智能任务调度器 v1.0
# 根据系统负载和资源情况智能调度自动化任务
# =============================================================================

set -e

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="/root/.openclaw/logs/smart-scheduler.log"
STATE_FILE="$WORKSPACE/memory/meta/smart-scheduler-state.json"

# 默认配置
CPU_THRESHOLD=70          # CPU使用率阈值(%)
MEMORY_THRESHOLD=80       # 内存使用率阈值(%)
DISK_THRESHOLD=85         # 磁盘使用率阈值(%)

# 初始化日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 获取系统资源状态
get_system_load() {
    # CPU使用率 (1分钟平均)
    local cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    local cpu_cores=$(nproc)
    local cpu_percent=$(echo "scale=0; $cpu_load * 100 / $cpu_cores" | bc -l 2>/dev/null || echo "50")
    
    # 内存使用率
    local mem_info=$(free | grep Mem)
    local mem_total=$(echo $mem_info | awk '{print $2}')
    local mem_used=$(echo $mem_info | awk '{print $3}')
    local mem_percent=$(echo "scale=0; $mem_used * 100 / $mem_total" | bc -l 2>/dev/null || echo "50")
    
    # 磁盘使用率
    local disk_percent=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
    
    echo "${cpu_percent%.*}|${mem_percent%.*}|$disk_percent"
}

# 检查系统是否适合执行任务
should_execute() {
    local priority=$1  # high/normal/low
    
    IFS='|' read -r cpu mem disk <<< "$(get_system_load)"
    
    log "当前资源状态: CPU=${cpu}% 内存=${mem}% 磁盘=${disk}%"
    
    # 高优先级任务总是执行
    if [ "$priority" = "high" ]; then
        return 0
    fi
    
    # 检查资源阈值
    if [ "$cpu" -gt "$CPU_THRESHOLD" ] || [ "$mem" -gt "$MEMORY_THRESHOLD" ]; then
        log "系统负载较高，跳过非高优先级任务"
        return 1
    fi
    
    if [ "$disk" -gt "$DISK_THRESHOLD" ]; then
        log "磁盘使用率过高，执行清理优先"
        return 2  # 特殊返回码：需要清理
    fi
    
    return 0
}

# 智能执行任务
smart_execute() {
    local task_name=$1
    local script_path=$2
    local priority=$3
    
    log "=" 
    log "调度任务: $task_name (优先级: $priority)"
    
    # 检查是否应该执行
    should_execute "$priority"
    local result=$?
    
    if [ $result -eq 1 ]; then
        log "⏭️  跳过: 系统负载高"
        return 0
    elif [ $result -eq 2 ]; then
        log "🧹 先执行磁盘清理"
        bash "$WORKSPACE/scripts/log-cleanup.sh" 2>/dev/null || true
    fi
    
    # 执行任务
    local start_time=$(date +%s)
    
    if [ -f "$script_path" ]; then
        if [[ "$script_path" == *.py ]]; then
            python3 "$script_path" >> "$LOG_FILE" 2>&1
        else
            bash "$script_path" >> "$LOG_FILE" 2>&1
        fi
        local exit_code=$?
    else
        log "❌ 脚本不存在: $script_path"
        return 1
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ]; then
        log "✅ 完成: ${duration}s"
    else
        log "❌ 失败 (exit $exit_code)"
    fi
    
    return $exit_code
}

# 执行一批任务
run_batch() {
    log "========================================"
    log "开始智能任务批次执行"
    log "========================================"
    
    # 高优先级任务 (总是执行)
    smart_execute "健康检查" "$WORKSPACE/scripts/health-check.sh" "high"
    smart_execute "向量记忆守护" "$WORKSPACE/scripts/memory-guardian.py" "high"
    
    # 普通优先级任务 (负载低时执行)
    smart_execute "记忆整理" "$WORKSPACE/scripts/memory-system/auto_consolidate.py" "normal"
    smart_execute "日志清理" "$WORKSPACE/scripts/log-cleanup.sh" "normal"
    
    # 低优先级任务 (仅系统空闲时)
    smart_execute "备份检查" "$WORKSPACE/scripts/backup-simple.sh" "low"
    
    log "========================================"
    log "批次执行完成"
    log "========================================"
}

# 生成调度报告
generate_report() {
    local report_file="$WORKSPACE/memory/reports/smart-scheduler-report.txt"
    mkdir -p "$(dirname "$report_file")"
    
    IFS='|' read -r cpu mem disk <<< "$(get_system_load)"
    
    cat > "$report_file" << EOF
智能调度器状态报告
==================
生成时间: $(date '+%Y-%m-%d %H:%M:%S')

系统资源
--------
CPU使用率: ${cpu}%
内存使用率: ${mem}%
磁盘使用率: ${disk}%

阈值配置
--------
CPU阈值: ${CPU_THRESHOLD}%
内存阈值: ${MEMORY_THRESHOLD}%
磁盘阈值: ${DISK_THRESHOLD}%

调度策略
--------
- 高优先级任务: 总是执行
- 普通优先级: CPU<
EOF
}

# 主函数
main() {
    mkdir -p "$(dirname "$LOG_FILE")"
    
    case "${1:-run}" in
        run)
            run_batch
            ;;
        status)
            IFS='|' read -r cpu mem disk <<< "$(get_system_load)"
            echo "系统资源: CPU=${cpu}% 内存=${mem}% 磁盘=${disk}%"
            ;;
        report)
            generate_report
            echo "报告已生成: $WORKSPACE/memory/reports/smart-scheduler-report.txt"
            ;;
        *)
            echo "用法: $0 [run|status|report]"
            exit 1
            ;;
    esac
}

main "$@"
