#!/bin/bash
# 月度压缩归档脚本
# 执行频率: 每月1日 02:00

WORKSPACE="/root/.openclaw/workspace"
ARCHIVE_DIR="$WORKSPACE/archive/monthly"
YEAR_MONTH=$(date +%Y%m)

mkdir -p "$ARCHIVE_DIR"

echo "[$(date)] 开始月度压缩归档..."

# 1. 压缩上个月的evolution报告
tar -czf "$ARCHIVE_DIR/evolution-reports-${YEAR_MONTH}.tar.gz" \
    -C "$WORKSPACE/memory/evolution" \
    $(find "$WORKSPACE/memory/evolution" -name "*.md" -mtime +30 -type f | sed "s|$WORKSPACE/memory/evolution/||" 2>/dev/null)

# 2. 压缩上个月的reports
find "$WORKSPACE/reports" -name "*.md" -mtime +30 -type f | tar -czf "$ARCHIVE_DIR/reports-${YEAR_MONTH}.tar.gz" -T -

# 3. 压缩vector数据快照 (保留最近3个月)
find "$WORKSPACE/memory/vector" -name "*.json" -mtime +90 -type f -delete

# 4. 生成归档报告
ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" | cut -f1)
echo "[$(date)] 月度归档完成，归档目录大小: $ARCHIVE_SIZE"

# 5. 清理90天前的月度归档
find "$ARCHIVE_DIR" -name "*.tar.gz" -mtime +90 -type f -delete

echo "[$(date)] 月度压缩归档完成"
