#!/bin/bash
# Unified Daily Maintenance - 合并维护任务
# 替代: log-cleanup-daily + daily-disk-cleanup + full-backup-daily

set -e

WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs"
BACKUP_DIR="$WORKSPACE/backups"
ARCHIVE_DIR="$WORKSPACE/archives"
DATE=$(date +%Y%m%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ===== 1. 日志清理 =====
echo "[$(date)] 开始日志清理..."

# 截断超过100MB的日志
find "$LOG_DIR" -name "*.log" -size +100M 2>/dev/null | while read logfile; do
    echo "截断大日志: $logfile"
    tail -n 1000 "$logfile" > "$logfile.tmp"
    mv "$logfile.tmp" "$logfile"
done

# 归档7天前的日志
find "$LOG_DIR" -name "*.log" -mtime +7 2>/dev/null | while read logfile; do
    mkdir -p "$ARCHIVE_DIR/logs"
    gzip -c "$logfile" > "$ARCHIVE_DIR/logs/$(basename $logfile).$DATE.gz"
    rm "$logfile"
    echo "归档日志: $logfile"
done

# 删除30天前的归档 - 确保目录存在
if [ -d "$ARCHIVE_DIR/logs" ]; then
    find "$ARCHIVE_DIR/logs" -name "*.gz" -mtime +30 -delete 2>/dev/null || true
fi

# 清理临时文件
find /tmp -name "openclaw_*" -mtime +1 -delete 2>/dev/null || true

echo "[$(date)] 日志清理完成"

# ===== 2. 磁盘清理 =====
echo "[$(date)] 开始磁盘清理..."

# 检查磁盘空间
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️ 磁盘使用率超过80% ($DISK_USAGE%)，执行深度清理"
    
    # 清理旧备份（保留最近10个）
    ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm
    
    # 清理旧归档
    find "$ARCHIVE_DIR" -type f -mtime +60 -delete 2>/dev/null || true
fi

# 清理Python缓存
find "$WORKSPACE" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$WORKSPACE" -name "*.pyc" -delete 2>/dev/null || true

echo "[$(date)] 磁盘清理完成"

# ===== 3. 完整备份 =====
echo "[$(date)] 开始完整备份..."

mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/workspace_backup_$TIMESTAMP.tar.gz"

# 创建完整备份（排除不必要的目录）
set +e
tar -czf "$BACKUP_FILE" --warning=no-file-changed \
    --exclude="backups" \
    --exclude="archives" \
    --exclude=".git" \
    --exclude="node_modules" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    -C "$(dirname $WORKSPACE)" \
    "$(basename $WORKSPACE)"
TAR_EXIT_CODE=$?
set -e

if [ $TAR_EXIT_CODE -ne 0 ]; then
    echo "⚠️ 备份完成但有警告 (退出码: $TAR_EXIT_CODE)"
else
    echo "✓ 备份成功完成"
fi

echo "[$(date)] 备份完成: $BACKUP_FILE"

# 保留最近10个备份
ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm
echo "[$(date)] 旧备份清理完成"

# ===== 4. 生成维护报告 =====
REPORT_FILE="$WORKSPACE/reports/maintenance_$TIMESTAMP.md"
mkdir -p "$WORKSPACE/reports"

cat > "$REPORT_FILE" << EOF
# 日常维护报告

**时间**: $(date)
**磁盘使用率**: ${DISK_USAGE}%
**备份文件**: $BACKUP_FILE

## 执行内容
- ✅ 日志清理
- ✅ 磁盘清理
- ✅ 完整备份

## 系统状态
$(df -h / | grep -v Filesystem)
EOF

echo "[$(date)] 维护报告: $REPORT_FILE"
echo "[$(date)] 统一维护任务完成"
