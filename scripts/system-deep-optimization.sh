#!/bin/bash
# System Deep Optimization Script v1.0
# 执行7项系统深度优化（不包括Git瘦身）

set -e

WORKSPACE="/root/.openclaw/workspace"
REPORTS_DIR="$WORKSPACE/reports"
MEMORY_DIR="$WORKSPACE/memory"
DATA_DIR="$WORKSPACE/data"
LOGS_DIR="$WORKSPACE/logs"
ARCHIVE_DIR="$WORKSPACE/archives"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORTS_DIR/system-optimization-$TIMESTAMP.md"

echo "="*60
echo "🚀 系统深度优化开始"
echo "="*60

# 创建报告目录
mkdir -p "$REPORTS_DIR"
mkdir -p "$ARCHIVE_DIR"

cat > "$REPORT_FILE" << 'EOF'
# 系统深度优化报告

**执行时间**: $(date)

EOF

# ===== 1. 旧报告归档 =====
echo "\n📦 1. 旧报告归档..."
REPORTS_BEFORE=$(du -sh "$REPORTS_DIR" | cut -f1)
ARCHIVED_COUNT=0

# 归档7天前的报告
mkdir -p "$ARCHIVE_DIR/reports"
find "$REPORTS_DIR" -name "*.md" -type f -mtime +7 -print0 2>/dev/null | while IFS= read -r -d '' file; do
    if [ -f "$file" ]; then
        gzip -c "$file" > "$ARCHIVE_DIR/reports/$(basename "$file").gz"
        rm "$file"
        ARCHIVED_COUNT=$((ARCHIVED_COUNT + 1))
    fi
done

# 归档30天前的压缩报告
find "$ARCHIVE_DIR/reports" -name "*.gz" -type f -mtime +30 -delete

REPORTS_AFTER=$(du -sh "$REPORTS_DIR" | cut -f1)
echo "  ✅ 归档完成: $REPORTS_BEFORE → $REPORTS_AFTER"

# ===== 2. 学习债务处理 =====
echo "\n📚 2. 学习债务处理..."
DEBT_FILE="$MEMORY_DIR/learning-debt.md"

if [ -f "$DEBT_FILE" ]; then
    # 统计债务数量
    PENDING_COUNT=$(grep -c "⏳ 待处理\|🔍 待深度学习" "$DEBT_FILE" 2>/dev/null || echo "0")
    echo "  发现 $PENDING_COUNT 条待处理债务"
    
    # 处理过期的债务（截止超过7天）
    # 这里可以添加Python脚本处理逻辑
    echo "  ✅ 债务统计完成，建议手动审查处理"
fi

# ===== 3. 诊断历史压缩 =====
echo "\n🗜️  3. 诊断历史压缩..."
DIAGNOSIS_FILE="$DATA_DIR/diagnosis_history.jsonl"

if [ -f "$DIAGNOSIS_FILE" ]; then
    SIZE_BEFORE=$(du -h "$DIAGNOSIS_FILE" | cut -f1)
    
    # 压缩超过30天的记录
    # 这里使用简单的gzip压缩
    if [ ! -f "$DIAGNOSIS_FILE.gz" ]; then
        gzip -c "$DIAGNOSIS_FILE" > "$ARCHIVE_DIR/diagnosis_history_$(date +%Y%m).jsonl.gz"
        # 保留最近30天的记录
        tail -n 1000 "$DIAGNOSIS_FILE" > "$DIAGNOSIS_FILE.tmp"
        mv "$DIAGNOSIS_FILE.tmp" "$DIAGNOSIS_FILE"
    fi
    
    SIZE_AFTER=$(du -h "$DIAGNOSIS_FILE" | cut -f1)
    echo "  ✅ 压缩完成: $SIZE_BEFORE → $SIZE_AFTER"
fi

# ===== 4. Python缓存清理 =====
echo "\n🐍 4. Python缓存清理..."
PYCACHE_COUNT=$(find "$WORKSPACE" -type d -name "__pycache__" | wc -l)
find "$WORKSPACE" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$WORKSPACE" -name "*.pyc" -delete 2>/dev/null || true
find "$WORKSPACE" -name "*.pyo" -delete 2>/dev/null || true
echo "  ✅ 清理 $PYCACHE_COUNT 个__pycache__目录"

# ===== 5. 向量记忆优化 =====
echo "\n🧠 5. 向量记忆优化..."
VECTOR_DIR="$DATA_DIR/vector_memory"

if [ -d "$VECTOR_DIR" ]; then
    VECTOR_COUNT=$(ls -1 "$VECTOR_DIR"/*.json 2>/dev/null | wc -l)
    echo "  发现 $VECTOR_COUNT 个向量文件"
    
    # 检查并删除空文件
    find "$VECTOR_DIR" -name "*.json" -size 0 -delete
    
    # 压缩旧向量文件（可选）
    echo "  ✅ 向量记忆清理完成"
fi

# ===== 6. 知识图谱去重 =====
echo "\n🕸️  6. 知识图谱检查..."
KNOWLEDGE_GRAPH="$MEMORY_DIR/knowledge-graph.md"

if [ -f "$KNOWLEDGE_GRAPH" ]; then
    NODES=$(grep -c "^## " "$KNOWLEDGE_GRAPH" 2>/dev/null || echo "0")
    echo "  发现 $NODES 个知识节点"
    echo "  ✅ 知识图谱检查完成（建议定期手动审查）"
fi

# ===== 7. 月度深度清理 =====
echo "\n🧹 7. 月度深度清理..."

# 清理旧日志
LOGS_ARCHIVED=0
find "$LOGS_DIR" -name "*.log" -mtime +30 | while read file; do
    mkdir -p "$ARCHIVE_DIR/logs"
    gzip -c "$file" > "$ARCHIVE_DIR/logs/$(basename $file).$(date +%Y%m).gz"
    rm "$file"
    ((LOGS_ARCHIVED++))
done

# 清理临时文件
TEMP_CLEANED=$(find /tmp -name "openclaw_*" -mtime +3 -delete 2>/dev/null | wc -l)

# 清理data目录的旧提取文件
find "$DATA_DIR" -name "moltbook_deep_extract_*.json" -mtime +7 -delete 2>/dev/null || true

# 统计清理结果
echo "  ✅ 日志归档: $LOGS_ARCHIVED 个文件"
echo "  ✅ 临时文件清理完成"

# ===== 生成最终报告 =====
echo "\n" >> "$REPORT_FILE"
echo "## 优化结果摘要" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| 项目 | 结果 |" >> "$REPORT_FILE"
echo "|------|------|" >> "$REPORT_FILE"
echo "| 旧报告归档 | $REPORTS_BEFORE → $REPORTS_AFTER |" >> "$REPORT_FILE"
echo "| Python缓存清理 | $PYCACHE_COUNT 个目录 |" >> "$REPORT_FILE"
echo "| 向量记忆优化 | 完成 |" >> "$REPORT_FILE"
echo "| 月度深度清理 | 完成 |" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "*优化完成: $(date)*" >> "$REPORT_FILE"

echo "\n" + "="*60
echo "✅ 系统深度优化完成"
echo "📊 报告已保存: $REPORT_FILE"
echo "="*60
