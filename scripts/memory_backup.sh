#!/bin/bash
# 记忆系统自动备份脚本 (Phase 3)

BACKUP_DIR="/root/.openclaw/workspace/data/vector_memory/backups"
DB_PATH="/root/.openclaw/workspace/data/vector_memory/memory.db"
LOG_FILE="/root/.openclaw/workspace/logs/memory-backup.log"

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/memory_backup_$TIMESTAMP.db"

# 创建备份
if cp "$DB_PATH" "$BACKUP_FILE"; then
    echo "$(date): ✅ 备份成功: $BACKUP_FILE" >> "$LOG_FILE"
    
    # 压缩备份
    gzip "$BACKUP_FILE"
    echo "$(date): ✅ 压缩完成: ${BACKUP_FILE}.gz" >> "$LOG_FILE"
    
    # 清理7天前的备份
    find "$BACKUP_DIR" -name "memory_backup_*.db.gz" -mtime +7 -delete
    echo "$(date): 🗑️  清理旧备份完成" >> "$LOG_FILE"
else
    echo "$(date): ❌ 备份失败" >> "$LOG_FILE"
    exit 1
fi
