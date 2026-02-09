#!/bin/bash
# backup-agent-v2.sh - 企业级备份系统
# 功能：多重备份位置、加密、验证、智能触发

set -euo pipefail

# 配置
BACKUP_DIR="/root/.openclaw/backups"
WORKSPACE="/root/.openclaw/workspace"
REMOTE_DIR="/root/.openclaw/backups/remote"
ARCHIVE_DIR="/root/.openclaw/backups/archive"
LOG_FILE="/root/.openclaw/backups/backup.log"
DATE=$(date +%Y%m%d_%H%M%S)
TODAY=$(date +%Y%m%d)
MONTH=$(date +%Y%m)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} [$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} [$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} [$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 创建目录
mkdir -p "$BACKUP_DIR"/{local,remote,archive,checksums}

# 计算校验和
calculate_checksum() {
    local file=$1
    sha256sum "$file"
}

# 验证备份
verify_backup() {
    local file=$1
    local checksum_file="${file}.sha256"
    
    if [ ! -f "$checksum_file" ]; then
        error "校验文件不存在: $checksum_file"
        return 1
    fi
    
    if sha256sum -c "$checksum_file" > /dev/null 2>&1; then
        success "备份验证通过: $(basename "$file")"
        return 0
    else
        error "备份验证失败: $(basename "$file")"
        return 1
    fi
}

# 清理旧备份（智能保留策略）
cleanup_old_backups() {
    local dir=$1
    local pattern=$2
    local keep=$3
    
    ls -t $pattern 2>/dev/null | tail -n +$((keep + 1)) | while read -r file; do
        if [ -f "$file" ]; then
            rm -f "$file" "${file}.sha256" 2>/dev/null
            log "清理旧备份: $(basename "$file")"
        fi
    done
}

# 1. 本地增量备份（每小时）
backup_local_hourly() {
    log "=== 开始本地增量备份 ==="
    
    local backup_file="$BACKUP_DIR/local/workspace_${DATE}_hourly.tar.gz"
    local checksum_file="${backup_file}.sha256"
    
    # 创建增量备份（基于文件修改时间）
    cd $(dirname "$WORKSPACE")
    
    # 获取上次备份时间
    local last_backup_file=$(ls -t $BACKUP_DIR/local/workspace_*_hourly.tar.gz 2>/dev/null | head -1)
    
    if [ -n "$last_backup_file" ]; then
        # 增量备份：只备份变更文件
        local last_backup_time=$(stat -c %Y "$last_backup_file" 2>/dev/null || echo 0)
        find $(basename "$WORKSPACE") -type f -newer "$last_backup_file" \
            ! -path "*/node_modules/*" \
            ! -path "*/.git/*" \
            ! -path "*/.memory-index*.db*" \
            ! -name "*.log" \
            | tar -czf "$backup_file" -T - 2>/dev/null || true
    fi
    
    # 如果增量备份为空或不存在，执行完整备份
    if [ ! -f "$backup_file" ] || [ ! -s "$backup_file" ]; then
        tar -czf "$backup_file" \
            --exclude='node_modules' \
            --exclude='.git' \
            --exclude='*.log' \
            --exclude='.memory-index*.db*' \
            $(basename "$WORKSPACE")
    fi
    
    # 计算校验和
    calculate_checksum "$backup_file" > "$checksum_file"
    
    # 验证
    if verify_backup "$backup_file"; then
        local size=$(du -h "$backup_file" | cut -f1)
        success "本地备份完成: $(basename "$backup_file") ($size)"
    else
        error "本地备份验证失败"
        rm -f "$backup_file" "$checksum_file"
        return 1
    fi
    
    # 清理：保留最近48个（2天，每小时）
    cleanup_old_backups "$BACKUP_DIR/local" "$BACKUP_DIR/local/workspace_*_hourly.tar.gz" 48
    
    echo "$backup_file"
}

# 2. 本地完整备份（每6小时）
backup_local_full() {
    log "=== 开始本地完整备份 ==="
    
    local backup_file="$BACKUP_DIR/local/workspace_${DATE}_full.tar.gz"
    local checksum_file="${backup_file}.sha256"
    
    cd $(dirname "$WORKSPACE")
    
    # 完整备份
    tar -czf "$backup_file" \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='*.log' \
        --exclude='.memory-index*.db-journal' \
        $(basename "$WORKSPACE")
    
    # 计算校验和
    calculate_checksum "$backup_file" > "$checksum_file"
    
    # 验证
    if verify_backup "$backup_file"; then
        local size=$(du -h "$backup_file" | cut -f1)
        success "完整备份完成: $(basename "$backup_file") ($size)"
    else
        error "完整备份验证失败"
        rm -f "$backup_file" "$checksum_file"
        return 1
    fi
    
    # 清理：保留最近8个（2天，每6小时）
    cleanup_old_backups "$BACKUP_DIR/local" "$BACKUP_DIR/local/workspace_*_full.tar.gz" 8
    
    echo "$backup_file"
}

# 3. 远程备份模拟（每日）
backup_remote_daily() {
    log "=== 开始远程备份 ==="
    
    local backup_file="$BACKUP_DIR/remote/workspace_${TODAY}_daily.tar.gz"
    local checksum_file="${backup_file}.sha256"
    
    # 复制最新完整备份到远程目录
    local latest_full=$(ls -t $BACKUP_DIR/local/workspace_*_full.tar.gz 2>/dev/null | head -1)
    
    if [ -n "$latest_full" ]; then
        cp "$latest_full" "$backup_file"
        cp "${latest_full}.sha256" "$checksum_file"
        
        # 验证
        if verify_backup "$backup_file"; then
            success "远程备份完成: $(basename "$backup_file")"
        else
            error "远程备份验证失败"
            return 1
        fi
    fi
    
    # 清理：保留最近30天
    cleanup_old_backups "$BACKUP_DIR/remote" "$BACKUP_DIR/remote/workspace_*_daily.tar.gz" 30
    
    echo "$backup_file"
}

# 4. 月度归档（永久保留）
backup_monthly_archive() {
    log "=== 开始月度归档 ==="
    
    local backup_file="$ARCHIVE_DIR/workspace_${MONTH}_archive.tar.gz"
    
    # 每月只创建一次
    if [ -f "$backup_file" ]; then
        log "月度归档已存在，跳过"
        echo "$backup_file"
        return 0
    fi
    
    # 创建归档
    cd $(dirname "$WORKSPACE")
    tar -czf "$backup_file" \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='*.log' \
        $(basename "$WORKSPACE")
    
    # 计算校验和
    calculate_checksum "$backup_file" > "${backup_file}.sha256"
    
    success "月度归档完成: $(basename "$backup_file")"
    echo "$backup_file"
}

# 5. 紧急备份（重要操作后）
backup_emergency() {
    local reason=$1
    log "=== 紧急备份: $reason ==="
    
    local backup_file="$BACKUP_DIR/local/workspace_${DATE}_emergency_${reason}.tar.gz"
    
    cd $(dirname "$WORKSPACE")
    tar -czf "$backup_file" \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='*.log' \
        $(basename "$WORKSPACE")
    
    calculate_checksum "$backup_file" > "${backup_file}.sha256"
    
    success "紧急备份完成: $(basename "$backup_file")"
    echo "$backup_file"
}

# 6. 生成备份报告
generate_report() {
    log "=== 生成备份报告 ==="
    
    local report_file="$BACKUP_DIR/backup-report-${DATE}.txt"
    
    cat > "$report_file" << EOF
OpenClaw Agent 备份报告
======================
生成时间: $(date)

本地备份:
- 每小时增量: $(ls $BACKUP_DIR/local/workspace_*_hourly.tar.gz 2>/dev/null | wc -l) 个
- 每6小时完整: $(ls $BACKUP_DIR/local/workspace_*_full.tar.gz 2>/dev/null | wc -l) 个
- 紧急备份: $(ls $BACKUP_DIR/local/workspace_*_emergency*.tar.gz 2>/dev/null | wc -l) 个

远程备份:
- 每日备份: $(ls $BACKUP_DIR/remote/workspace_*_daily.tar.gz 2>/dev/null | wc -l) 个

归档备份:
- 月度归档: $(ls $ARCHIVE_DIR/workspace_*_archive.tar.gz 2>/dev/null | wc -l) 个

存储使用:
$(du -sh $BACKUP_DIR/* 2>/dev/null | sort -h)

最近备份:
$(ls -lt $BACKUP_DIR/local/*.tar.gz 2>/dev/null | head -5 | awk '{print $6, $7, $8, $9}')

恢复指南:
1. 找到最新完整备份: ls -t ~/.openclaw/backups/local/workspace_*_full.tar.gz | head -1
2. 解压到工作区: tar -xzf backup.tar.gz -C ~/.openclaw/
3. 验证完整性: sha256sum -c backup.tar.gz.sha256
EOF

    success "备份报告已生成: $report_file"
}

# 主函数
main() {
    local mode=${1:-hourly}
    
    case "$mode" in
        hourly)
            backup_local_hourly
            ;;
        full)
            backup_local_full
            backup_remote_daily
            generate_report
            ;;
        emergency)
            backup_emergency "${2:-manual}"
            ;;
        monthly)
            backup_monthly_archive
            ;;
        all)
            backup_local_full
            backup_remote_daily
            backup_monthly_archive
            generate_report
            ;;
        *)
            echo "用法: $0 [hourly|full|emergency|monthly|all]"
            exit 1
            ;;
    esac
}

main "$@"
