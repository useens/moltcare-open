#!/bin/bash
# Token黑洞清理脚本 - 立即执行版
# 执行时间: $(date '+%Y-%m-%d %H:%M:%S')

LOG_DIR="/root/.openclaw/workspace/logs"
REPORTS_DIR="/root/.openclaw/workspace/reports"
MEMORY_DIR="/root/.openclaw/workspace/memory"

echo "========================================"
echo "🧹 Token黑洞清理开始"
echo "========================================"

# 1. 日志截断 - 只保留ERROR级别和最后100行
echo ""
echo "📋 步骤1: 日志文件截断"
echo "   原大小:"
du -sh $LOG_DIR

# 截断大日志文件（保留最后100行）
for logfile in $LOG_DIR/*.log; do
    if [ -f "$logfile" ] && [ $(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile" 2>/dev/null || echo 0) -gt 102400 ]; then
        tail -100 "$logfile" > "$logfile.tmp"
        mv "$logfile.tmp" "$logfile"
        echo "   ✅ 截断: $(basename $logfile)"
    fi
done

echo "   新大小:"
du -sh $LOG_DIR

# 2. 归档旧报告（30天前）
echo ""
echo "📋 步骤2: 旧报告归档"
echo "   原大小:"
du -sh $REPORTS_DIR

mkdir -p $REPORTS_DIR/archive
find $REPORTS_DIR -maxdepth 1 -name "*.md" -mtime +30 -exec gzip {} \; -exec mv {}.gz $REPORTS_DIR/archive/ \; 2>/dev/null

echo "   新大小:"
du -sh $REPORTS_DIR

# 3. 清理旧daily文件（90天前）
echo ""
echo "📋 步骤3: 旧daily文件清理"
mkdir -p $MEMORY_DIR/archive/daily
find $MEMORY_DIR -maxdepth 1 -name "2025-*.md" -mtime +90 -exec mv {} $MEMORY_DIR/archive/daily/ \; 2>/dev/null
echo "   ✅ 已归档90天前的daily文件"

# 4. 压缩archive目录
echo ""
echo "📋 步骤4: 压缩归档文件"
find $MEMORY_DIR/archive -name "*.md" -mtime +7 -exec gzip -f {} \; 2>/dev/null
echo "   ✅ 已压缩7天前的归档文件"

echo ""
echo "========================================"
echo "✅ Token黑洞清理完成"
echo "========================================"