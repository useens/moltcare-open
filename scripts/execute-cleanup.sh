#!/bin/bash
# 316脚本清理执行脚本 - 阶段1+2+3
# 基于深度审计报告: reports/script-audit-deep.md

WORKSPACE=/root/.openclaw/workspace
SCRIPTS=$WORKSPACE/scripts
ARCHIVE=$SCRIPTS/.archive
REPORTS=$WORKSPACE/reports

echo "🧹 316脚本清理执行"
echo "==================="
echo ""
echo "基于深度审计报告: reports/script-audit-deep.md"
echo ""

# 创建备份和归档目录
mkdir -p $ARCHIVE/capability-experiments
mkdir -p $ARCHIVE/old-moltbook
mkdir -p $ARCHIVE/temp-fixes
mkdir -p $SCRIPTS/tests
mkdir -p $REPORTS/deleted

# 记录清理日志
LOG_FILE=$REPORTS/cleanup-$(date +%Y%m%d-%H%M%S).log
echo "清理日志: $LOG_FILE"
echo "开始时间: $(date -Iseconds)" > $LOG_FILE
echo "" >> $LOG_FILE

# ========== 阶段1: 安全删除 (13个，0风险) ==========
echo ""
echo "📦 阶段1: 安全删除 (13个，0风险)"
echo "-----------------------------------"

# 1. 临时修复脚本 (7个)
TEMP_SCRIPTS=(
    "fix-and-run.py"
    "fix_import_optimized.py"
    "fix_import_standalone.py"
    "fix_import_v2.py"
    "fix_memory_import.py"
    "verify-fix.py"
    "verify_logger.py"
)

for script in "${TEMP_SCRIPTS[@]}"; do
    if [ -f "$SCRIPTS/$script" ]; then
        echo "  归档: $script"
        mv "$SCRIPTS/$script" $ARCHIVE/temp-fixes/
        echo "ARCHIVED: $script" >> $LOG_FILE
    fi
done

# 2. 重复命名 (2个)
DUPLICATE_SCRIPTS=(
    "token_optimizer_v10.py"
    "state-snapshot-drift-v1-backup-20260216.py"
)

for script in "${DUPLICATE_SCRIPTS[@]}"; do
    if [ -f "$SCRIPTS/$script" ]; then
        echo "  删除: $script"
        echo "DELETED: $script (duplicate)" >> $LOG_FILE
        rm "$SCRIPTS/$script"
    fi
done

# 3. 明显无用脚本 (4个)
USELESS_SCRIPTS=(
    "ai-consulting-service.py"
    "random_numbers.py"
    "browser-automation-demo.py"
    "execute_full_learning_cycle.py"
)

for script in "${USELESS_SCRIPTS[@]}"; do
    if [ -f "$SCRIPTS/$script" ]; then
        echo "  删除: $script"
        echo "DELETED: $script (useless)" >> $LOG_FILE
        rm "$SCRIPTS/$script"
    fi
done

# ========== 阶段2: Moltbook版本清理 (14个，低风险) ==========
echo ""
echo "📱 阶段2: Moltbook旧版本清理 (14个)"
echo "------------------------------------"
echo "保留: v60, v61, v71"

OLD_MOLTBOOK_VERSIONS=(
    "moltbook_social_v7.py"
    "moltbook_social_v8.py"
    "moltbook_social_v21.py"
    "moltbook_social_v30.py"
    "moltbook_social_v31.py"
    "moltbook_social_v32.py"
    "moltbook_social_v32_clean.py"
    "moltbook_social_v33.py"
    "moltbook_social_v34.py"
    "moltbook_social_v40.py"
    "moltbook_social_v41.py"
    "moltbook_social_v50.py"
    "moltbook_social_v51.py"
    "moltbook_social_v62.py"
)

for script in "${OLD_MOLTBOOK_VERSIONS[@]}"; do
    if [ -f "$SCRIPTS/$script" ]; then
        echo "  归档: $script"
        mv "$SCRIPTS/$script" $ARCHIVE/old-moltbook/
        echo "ARCHIVED: $script (old version)" >> $LOG_FILE
    fi
done

# 阶段2b: 其他旧版Moltbook脚本
echo ""
echo "  其他旧版Moltbook脚本:"
OLD_MOLTBOOK_OTHERS=(
    "fetch_moltbook.py"
    "fetch_moltbook_v2.py"
    "fetch-moltbook-simple.py"
    "fetch-moltbook-spa.py"
    "moltbook_process.py"
    "moltbook_process_v72.py"
    "moltbook_generate_v61.py"
    "moltbook_sender_v60.py"
    "moltbook_scanner_v60.py"
    "fetch_silicon_zoo.py"
)

for script in "${OLD_MOLTBOOK_OTHERS[@]}"; do
    if [ -f "$SCRIPTS/$script" ]; then
        echo "    归档: $script"
        mv "$SCRIPTS/$script" $ARCHIVE/old-moltbook/
        echo "ARCHIVED: $script (old moltbook)" >> $LOG_FILE
    fi
done

# ========== 阶段3: 归档能力突破实验 (15个) ==========
echo ""
echo "🚀 阶段3: 归档能力突破实验 (15个)"
echo "----------------------------------"

for i in $(seq -w 1 15); do
    script="capability-breakthrough-exp-${i}.py"
    if [ -f "$SCRIPTS/$script" ]; then
        echo "  归档: $script"
        mv "$SCRIPTS/$script" $ARCHIVE/capability-experiments/
        echo "ARCHIVED: $script" >> $LOG_FILE
    fi
done

# ========== 阶段4: 移动测试脚本 (13个) ==========
echo ""
echo "🧪 阶段4: 移动测试脚本到 tests/ (13个)"
echo "----------------------------------------"

TEST_SCRIPTS=(
    "test-30-sources-concurrent.py"
    "test-adaptive-frequency.py"
    "test-daemon.py"
    "test_memory_service.py"
    "test-moltbook-insights.py"
    "test-moltbook-integration.py"
    "test-moltbook-round2.py"
    "test-multi-round-chat.py"
    "test_nanobot_nodes.py"
    "test_uuid_fix.py"
    "test_vector_integration.py"
    "test_vector_queries.py"
    "test_ws_realtime.py"
)

for script in "${TEST_SCRIPTS[@]}"; do
    if [ -f "$SCRIPTS/$script" ]; then
        echo "  移动: $script → tests/"
        mv "$SCRIPTS/$script" $SCRIPTS/tests/
        echo "MOVED: $script → tests/" >> $LOG_FILE
    fi
done

# ========== 统计 ==========
echo ""
echo "📊 清理统计"
echo "==========="

BEFORE=316
AFTER=$(ls $SCRIPTS/*.py 2>/dev/null | wc -l)
DELETED=$((BEFORE - AFTER))
ARCHIVED=$(find $ARCHIVE -name "*.py" 2>/dev/null | wc -l)
MOVED=$(ls $SCRIPTS/tests/*.py 2>/dev/null | wc -l)

echo "清理前: $BEFORE 个脚本"
echo "清理后: $AFTER 个脚本"
echo "减少: $DELETED 个 ($(echo "scale=1; $DELETED * 100 / $BEFORE" | bc)%)"
echo "归档: $ARCHIVED 个"
echo "移至tests/: $MOVED 个"
echo ""

echo "结束时间: $(date -Iseconds)" >> $LOG_FILE
echo "清理后脚本数: $AFTER" >> $LOG_FILE

echo "✅ 清理完成"
echo "日志文件: $LOG_FILE"
