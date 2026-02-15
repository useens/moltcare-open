#!/bin/bash
# 记忆压缩归档脚本
# 用途: 定期压缩旧记忆文件，降低Token消耗
# 执行频率: 每日

set -e

WORKSPACE="/root/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"
ARCHIVE_DIR="$MEMORY_DIR/archive"
DATE=$(date +%Y%m%d)

echo "🗜️ 记忆压缩归档启动: $DATE"

# 1. 归档7天前的daily文件
find "$MEMORY_DIR" -maxdepth 1 -name "2026-*.md" -mtime +7 -type f 2>/dev/null | while read file; do
    if [[ "$file" != *"$(date +%Y-%m-%d)"* ]]; then
        mv "$file" "$ARCHIVE_DIR/daily/"
        echo "  归档: $(basename $file)"
    fi
done

# 2. 压缩30天前的归档
find "$ARCHIVE_DIR/daily" -name "*.md" -mtime +30 -type f 2>/dev/null | while read file; do
    gzip -f "$file"
    echo "  压缩: $(basename $file).gz"
done

# 3. 清理90天前的压缩文件
find "$ARCHIVE_DIR/daily" -name "*.gz" -mtime +90 -type f -delete 2>/dev/null

# 4. 生成压缩报告
DAILY_COUNT=$(ls -1 "$ARCHIVE_DIR/daily" 2>/dev/null | wc -l)
CURRENT_SIZE=$(du -sh "$MEMORY_DIR" | cut -f1)

echo "✅ 归档完成"
echo "  归档文件数: $DAILY_COUNT"
echo "  当前记忆大小: $CURRENT_SIZE"

# 记录到日志
echo "[$DATE] 归档: $DAILY_COUNT 文件, 当前大小: $CURRENT_SIZE" >> "$MEMORY_DIR/archive/compression-log.txt"
