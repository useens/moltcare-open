#!/bin/bash
# =============================================================================
# 林林健康检查脚本 - Health Check Script
# 每2小时运行一次，仅异常时输出告警信息
# =============================================================================

set -e

# 配置
ALERT_DISK_THRESHOLD=80      # 磁盘使用率告警阈值(%)
ALERT_MEMORY_THRESHOLD=90    # 内存使用率告警阈值(%)
ALERT_SYNC_DELAY=3600        # GitHub同步延迟告警阈值(秒)
GITHUB_REPO="useens/linlin-backup"
WORKSPACE_DIR="${HOME}/.openclaw/workspace"

# 状态收集
STATUS="OK"
ALERTS=()
WARNINGS=()
INFO=()

# 检查磁盘空间
check_disk() {
    local usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    if [ "$usage" -gt "$ALERT_DISK_THRESHOLD" ]; then
        ALERTS+=("磁盘空间告警: ${usage}% 已使用 (阈值: ${ALERT_DISK_THRESHOLD}%)")
        STATUS="ALERT"
    elif [ "$usage" -gt $((ALERT_DISK_THRESHOLD - 10)) ]; then
        WARNINGS+=("磁盘空间警告: ${usage}% 已使用")
    fi
    INFO+=("磁盘使用: ${usage}%")
}

# 检查内存
check_memory() {
    local usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$usage" -gt "$ALERT_MEMORY_THRESHOLD" ]; then
        ALERTS+=("内存使用告警: ${usage}% (阈值: ${ALERT_MEMORY_THRESHOLD}%)")
        STATUS="ALERT"
    fi
    INFO+=("内存使用: ${usage}%")
}

# 检查 GitHub 同步状态
check_github_sync() {
    if [ -d "${WORKSPACE_DIR}/.git" ]; then
        cd "${WORKSPACE_DIR}"
        
        # 获取最后一次提交时间
        local last_commit_time=$(git log -1 --format=%ct 2>/dev/null || echo "0")
        local current_time=$(date +%s)
        local time_diff=$((current_time - last_commit_time))
        
        if [ "$time_diff" -gt "$ALERT_SYNC_DELAY" ]; then
            local hours=$((time_diff / 3600))
            ALERTS+=("GitHub同步延迟: 最后提交 ${hours}小时前 (阈值: $((ALERT_SYNC_DELAY/3600))小时)")
            STATUS="ALERT"
        fi
        
        # 检查是否有未推送的提交
        local unpushed=$(git log origin/main..HEAD --oneline 2>/dev/null | wc -l)
        if [ "$unpushed" -gt 0 ]; then
            WARNINGS+=("有 ${unpushed} 个提交未推送到 GitHub")
        fi
        
        local last_commit=$(git log -1 --format="%H" 2>/dev/null | cut -c1-7)
        INFO+=("GitHub: 最后提交 ${last_commit} ($((time_diff/60))分钟前)")
    else
        ALERTS+=("workspace 不是 git 仓库")
        STATUS="ALERT"
    fi
}

# 检查向量记忆系统
check_vector_memory() {
    local vector_db="${WORKSPACE_DIR}/memory/vector-memory.db"
    if [ -f "$vector_db" ]; then
        local size=$(du -h "$vector_db" 2>/dev/null | cut -f1)
        INFO+=("向量记忆: ${size}")
    else
        # 向量记忆系统可能不存在或路径不同，仅作为信息而非警告
        INFO+=("向量记忆: 未检测到")
    fi
}

# 检查关键进程
check_processes() {
    if pgrep -f "openclaw" > /dev/null 2>&1; then
        INFO+=("OpenClaw: 运行中")
    else
        ALERTS+=("OpenClaw 网关未运行")
        STATUS="ALERT"
    fi
}

# 检查备份状态
check_backups() {
    local backup_dir="${HOME}/.openclaw/backups"
    if [ -d "$backup_dir" ]; then
        local backup_count=$(ls -1 "$backup_dir"/*.tar.gz 2>/dev/null | wc -l)
        local latest_backup=$(ls -1t "$backup_dir"/*.tar.gz 2>/dev/null | head -1)
        
        if [ -n "$latest_backup" ]; then
            local latest_time=$(stat -c %Y "$latest_backup" 2>/dev/null || echo "0")
            local current_time=$(date +%s)
            local diff=$((current_time - latest_time))
            
            if [ "$diff" -gt 86400 ]; then
                WARNINGS+=("本地备份超过24小时未更新")
            fi
            
            INFO+=("本地备份: ${backup_count}个")
        fi
    fi
}

# 生成报告
generate_report() {
    echo "=== 林林健康检查报告 ==="
    echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "主机: $(hostname)"
    echo "状态: ${STATUS}"
    echo ""
    
    if [ ${#ALERTS[@]} -gt 0 ]; then
        echo "【告警】"
        for alert in "${ALERTS[@]}"; do
            echo "  ⚠️  ${alert}"
        done
        echo ""
    fi
    
    if [ ${#WARNINGS[@]} -gt 0 ]; then
        echo "【警告】"
        for warn in "${WARNINGS[@]}"; do
            echo "  ⚡ ${warn}"
        done
        echo ""
    fi
    
    echo "【状态信息】"
    for info in "${INFO[@]}"; do
        echo "  ✓ ${info}"
    done
}

# 主程序
main() {
    check_disk
    check_memory
    check_github_sync
    check_vector_memory
    check_processes
    check_backups
    
    # 静默模式: 只有告警或警告时才输出
    if [ "$STATUS" = "ALERT" ] || [ ${#WARNINGS[@]} -gt 0 ] || [ "$1" = "--verbose" ]; then
        generate_report
        exit 1  # 异常退出码，便于 cron 通知
    else
        # 完全静默，仅在 verbose 模式输出
        if [ "$1" = "--verbose" ]; then
            generate_report
        fi
        exit 0
    fi
}

main "$@"
