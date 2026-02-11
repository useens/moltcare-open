#!/bin/bash
#
# 日志清理脚本 v1.0
# 定期清理各类日志，防止无限增长
#

set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
LOGS_DIR="/root/.openclaw/logs"
MAX_LOG_SIZE_MB=100           # 单个日志文件最大100MB
MAX_LOG_AGE_DAYS=30           # 日志保留30天
ARCHIVE_DAYS=7                # 7天前的日志归档压缩

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 清理超过大小限制的日志文件
cleanup_oversized_logs() {
    log "检查超大日志文件..."
    find "$LOGS_DIR" -type f -name "*.log" -size +${MAX_LOG_SIZE_MB}M 2>/dev/null | while read -r logfile; do
        log "  截断超大日志: $(basename "$logfile")"
        # 保留最后1000行
        tail -n 1000 "$logfile" > "${logfile}.tmp"
        mv "${logfile}.tmp" "$logfile"
    done
}

# 归档旧日志
archive_old_logs() {
    log "归档旧日志..."
    local archive_dir="${LOGS_DIR}/archive"
    mkdir -p "$archive_dir"
    
    find "$LOGS_DIR" -maxdepth 1 -type f -name "*.log" -mtime +$ARCHIVE_DAYS 2>/dev/null | while read -r logfile; do
        local filename=$(basename "$logfile")
        local archive_name="${filename%.log}_$(date -r "$logfile" '+%Y%m%d').log.gz"
        log "  归档: $filename → $archive_name"
        gzip -c "$logfile" > "${archive_dir}/${archive_name}"
        rm -f "$logfile"
    done
}

# 删除过期的归档文件
cleanup_old_archives() {
    log "清理过期归档..."
    local archive_dir="${LOGS_DIR}/archive"
    
    if [ -d "$archive_dir" ]; then
        find "$archive_dir" -type f -name "*.gz" -mtime +$MAX_LOG_AGE_DAYS -delete 2>/dev/null || true
        local remaining=$(find "$archive_dir" -type f 2>/dev/null | wc -l)
        log "  归档目录剩余文件: $remaining"
    fi
}

# 清理临时文件
cleanup_temp_files() {
    log "清理临时文件..."
    # 清理 /tmp 下超过1天的临时文件
    find /tmp -maxdepth 1 -type f -name "vm_last_notify" -mtime +1 -delete 2>/dev/null || true
    find /tmp -maxdepth 1 -type f -name "tg_notify_*" -mtime +1 -delete 2>/dev/null || true
}

# 主函数
main() {
    log "===== 日志清理开始 ====="
    
    mkdir -p "$LOGS_DIR"
    
    local before_size=$(du -sh "$LOGS_DIR" 2>/dev/null | cut -f1)
    log "清理前大小: $before_size"
    
    cleanup_oversized_logs
    archive_old_logs
    cleanup_old_archives
    cleanup_temp_files
    
    local after_size=$(du -sh "$LOGS_DIR" 2>/dev/null | cut -f1)
    log "清理后大小: $after_size"
    
    log "===== 日志清理完成 ====="
}

main "$@"
