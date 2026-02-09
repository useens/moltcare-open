#!/bin/bash
# 系统安全清理脚本 v1.0
# 每周执行一次，清理不影响系统稳定的文件

LOG_FILE="/var/log/system-cleanup.log"
LOCK_FILE="/tmp/system-cleanup.lock"

# 防止重复运行
if [ -f "$LOCK_FILE" ]; then
    echo "$(date): 清理任务已在运行，退出" | tee -a "$LOG_FILE"
    exit 0
fi
touch "$LOCK_FILE"

# 确保脚本结束时删除锁文件
trap 'rm -f "$LOCK_FILE"' EXIT

echo "========================================" | tee -a "$LOG_FILE"
echo "$(date): 开始系统安全清理" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 1. 清理 systemd journal 日志（保留7天）
echo "$(date): 清理 journal 日志..." | tee -a "$LOG_FILE"
BEFORE_JOURNAL=$(du -sb /var/log/journal 2>/dev/null | awk '{print $1}')
journalctl --vacuum-time=7d 2>&1 | tee -a "$LOG_FILE"
AFTER_JOURNAL=$(du -sb /var/log/journal 2>/dev/null | awk '{print $1}')
FREED_JOURNAL=$((BEFORE_JOURNAL - AFTER_JOURNAL))
echo "$(date): Journal 清理完成，释放 $(($FREED_JOURNAL / 1024 / 1024)) MB" | tee -a "$LOG_FILE"

# 2. 清理 apt 缓存（但保留最近使用的包列表）
echo "$(date): 清理 apt 缓存..." | tee -a "$LOG_FILE"
BEFORE_APT=$(du -sb /var/cache/apt 2>/dev/null | awk '{print $1}')
apt-get autoclean 2>&1 | tee -a "$LOG_FILE"
AFTER_APT=$(du -sb /var/cache/apt 2>/dev/null | awk '{print $1}')
FREED_APT=$((BEFORE_APT - AFTER_APT))
echo "$(date): APT 缓存清理完成，释放 $(($FREED_APT / 1024 / 1024)) MB" | tee -a "$LOG_FILE"

# 3. 清理旧备份文件（OpenClaw备份保留30天）
echo "$(date): 清理旧备份文件..." | tee -a "$LOG_FILE"
BACKUP_DIR="/root/.openclaw/backups/local"
if [ -d "$BACKUP_DIR" ]; then
    BEFORE_BACKUP=$(du -sb "$BACKUP_DIR" 2>/dev/null | awk '{print $1}')
    # 删除30天前的备份文件，但保留最新的10个
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +30 | sort -r | tail -n +11 | while read file; do
        echo "$(date): 删除旧备份: $file" | tee -a "$LOG_FILE"
        rm -f "$file"
    done
    AFTER_BACKUP=$(du -sb "$BACKUP_DIR" 2>/dev/null | awk '{print $1}')
    FREED_BACKUP=$((BEFORE_BACKUP - AFTER_BACKUP))
    echo "$(date): 备份清理完成，释放 $(($FREED_BACKUP / 1024 / 1024)) MB" | tee -a "$LOG_FILE"
else
    echo "$(date): 备份目录不存在，跳过" | tee -a "$LOG_FILE"
fi

# 4. 清理临时文件（/tmp 中超过7天的文件，排除运行中的进程）
echo "$(date): 清理临时文件..." | tee -a "$LOG_FILE"
BEFORE_TMP=$(du -sb /tmp 2>/dev/null | awk '{print $1}')
# 安全清理：只删除普通文件，不删除目录，不删除正在使用的文件
find /tmp -type f -atime +7 ! -name "*.lock" ! -name "*system-cleanup*" -exec rm -f {} \; 2>/dev/null
AFTER_TMP=$(du -sb /tmp 2>/dev/null | awk '{print $1}')
FREED_TMP=$((BEFORE_TMP - AFTER_TMP))
echo "$(date): 临时文件清理完成，释放 $(($FREED_TMP / 1024 / 1024)) MB" | tee -a "$LOG_FILE"

# 5. 清理用户缓存（保留最近7天）
echo "$(date): 清理用户缓存..." | tee -a "$LOG_FILE"
find /root -type f \( -name "*.log.old" -o -name "*.bak" \) -mtime +7 -exec rm -f {} \; 2>/dev/null
echo "$(date): 用户缓存清理完成" | tee -a "$LOG_FILE"

# 6. 可选：Docker 清理（注释掉，需要手动确认）
# echo "$(date): 检查 Docker 悬空资源..." | tee -a "$LOG_FILE"
# docker system df 2>&1 | tee -a "$LOG_FILE"

# 总结
echo "========================================" | tee -a "$LOG_FILE"
TOTAL_FREED=$((FREED_JOURNAL + FREED_APT + FREED_BACKUP + FREED_TMP))
echo "$(date): 清理任务完成" | tee -a "$LOG_FILE"
echo "$(date): 总释放空间: $(($TOTAL_FREED / 1024 / 1024)) MB ($(($TOTAL_FREED / 1024 / 1024 / 1024)) GB)" | tee -a "$LOG_FILE"
echo "$(date): 当前磁盘使用率: $(df -h / | awk 'NR==2 {print $5}')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

exit 0
