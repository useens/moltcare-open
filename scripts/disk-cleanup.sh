#!/bin/bash
# 森森磁盘清理脚本 - 自动维护策略
# 执行频率: 每日 03:00
# 范围: Workspace + 服务器系统级清理

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/disk-cleanup.log"
ARCHIVE_DIR="$WORKSPACE/archive"

mkdir -p "$ARCHIVE_DIR"
echo "[$(date)] 开始磁盘清理 (Workspace + System)..." >> "$LOG_FILE"

# ==================== 系统级清理 ====================

# 1. 清理Apt缓存 (保留最近7天)
if [ -d "/var/cache/apt/archives" ]; then
    APT_CACHE_SIZE=$(du -sh /var/cache/apt/archives 2>/dev/null | cut -f1)
    echo "[$(date)] Apt缓存清理前: $APT_CACHE_SIZE" >> "$LOG_FILE"
    apt-get autoclean >/dev/null 2>&1
    apt-get clean >/dev/null 2>&1
    echo "[$(date)] Apt缓存已清理" >> "$LOG_FILE"
fi

# 2. 轮替并压缩系统日志
if [ -d "/var/log" ]; then
    # 压缩7天前的.log文件
    find /var/log -name "*.log" -mtime +7 -type f ! -name "*$(date +%Y%m%d)*" -exec gzip -f {} \; 2>/dev/null
    # 删除30天前的.gz日志
    find /var/log -name "*.gz" -mtime +30 -type f -delete 2>/dev/null
    echo "[$(date)] 系统日志已清理" >> "$LOG_FILE"
fi

# 3. 清理Journal日志 (保留最近7天)
if command -v journalctl >/dev/null 2>&1; then
    JOURNAL_SIZE_BEFORE=$(journalctl --disk-usage 2>/dev/null | grep -oP '\d+\.?\d*M' | head -1)
    journalctl --vacuum-time=7d --quiet 2>/dev/null
    JOURNAL_SIZE_AFTER=$(journalctl --disk-usage 2>/dev/null | grep -oP '\d+\.?\d*M' | head -1)
    echo "[$(date)] Journal日志: $JOURNAL_SIZE_BEFORE -> $JOURNAL_SIZE_AFTER" >> "$LOG_FILE"
fi

# 4. 清理临时文件
find /tmp -type f -mtime +3 -delete 2>/dev/null
find /var/tmp -type f -mtime +3 -delete 2>/dev/null
echo "[$(date)] 临时文件已清理" >> "$LOG_FILE"

# 5. 清理旧的flatpak/snaps (如果存在)
if command -v snap >/dev/null 2>&1; then
    snap list --all | awk '/disabled/{print $1, $3}' | while read snapname revision; do
        snap remove "$snapname" --revision="$revision" 2>/dev/null
    done
fi

# ==================== Workspace清理 ====================

# 1. 清理7天前的reports/*.md (保留最近7天)
find "$WORKSPACE/reports" -name "*.md" -mtime +7 -type f | while read f; do
    gzip -c "$f" > "$ARCHIVE_DIR/$(basename $f).gz" && rm "$f"
    echo "[$(date)] 归档: $f" >> "$LOG_FILE"
done

# 2. 清理14天前的data/moltbook/*.json (原始数据)
find "$WORKSPACE/data/moltbook" -name "*.json" -mtime +14 -type f -delete
find "$WORKSPACE/data/hackernews" -name "*.json" -mtime +14 -type f -delete
find "$WORKSPACE/data/github_trending" -name "*.json" -mtime +14 -type f -delete
echo "[$(date)] 清理14天前原始数据" >> "$LOG_FILE"

# 3. 清理30天前的evolution报告 (保留最近30天)
find "$WORKSPACE/memory/evolution" -name "*.md" -mtime +30 -type f | while read f; do
    tar -czf "$ARCHIVE_DIR/evolution-$(date +%Y%m).tar.gz" "$f" && rm "$f"
done
echo "[$(date)] 归档30天前evolution报告" >> "$LOG_FILE"

# 4. 清理7天前的snapshots (保留最近7天)
find "$WORKSPACE/memory/snapshots" -name "*.json" -mtime +7 -type f -delete
echo "[$(date)] 清理7天前snapshots" >> "$LOG_FILE"

# 5. 清理3天前的dashboard (可视化dashboard)
find "$WORKSPACE/memory/visualizations" -name "dashboard_*.txt" -mtime +3 -type f -delete
echo "[$(date)] 清理3天前dashboard" >> "$LOG_FILE"

# 6. 压缩3天前的logs/*.log
find "$WORKSPACE/logs" -name "*.log" -mtime +3 -type f | while read f; do
    gzip -f "$f"
    echo "[$(date)] 压缩: $f" >> "$LOG_FILE"
done

# 7. 清理archive目录中超过90天的归档
find "$ARCHIVE_DIR" -name "*.gz" -mtime +90 -type f -delete
find "$ARCHIVE_DIR" -name "*.tar.gz" -mtime +90 -type f -delete
echo "[$(date)] 清理90天前归档" >> "$LOG_FILE"

# 8. 磁盘使用报告
DISK_USAGE=$(df -h /root | awk 'NR==2 {print $5}' | tr -d '%')
echo "[$(date)] 当前磁盘使用率: ${DISK_USAGE}%" >> "$LOG_FILE"

# 如果磁盘>80%，发送警告并深度清理
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "[$(date)] ⚠️ 磁盘使用率超过80%，执行深度清理..." >> "$LOG_FILE"
    # 深度清理：删除30天前的所有归档
    find "$ARCHIVE_DIR" -type f -mtime +30 -delete
    # 删除所有非当天的详细debug日志
    find "$WORKSPACE/logs" -name "*debug*.log" -mtime +1 -delete
fi

# ==================== 系统级磁盘监控 ====================
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
DISK_AVAIL=$(df -h / | awk 'NR==2 {print $4}')
echo "[$(date)] 系统磁盘: ${DISK_USAGE}% 已用, $DISK_AVAIL 剩余" >> "$LOG_FILE"

# 如果磁盘>75%，发送警告
if [ "$DISK_USAGE" -gt 75 ]; then
    echo "[$(date)] ⚠️ 警告: 系统磁盘使用率超过75%" >> "$LOG_FILE"
fi

echo "[$(date)] 磁盘清理完成" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
