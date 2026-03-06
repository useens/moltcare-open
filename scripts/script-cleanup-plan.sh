#!/bin/bash
# script-cleanup-plan.sh
# 316脚本清理执行计划
# ⚠️ 先审核再执行

WORKSPACE=/root/.openclaw/workspace
SCRIPTS=$WORKSPACE/scripts
ARCHIVE=$SCRIPTS/.archive

echo "🧹 脚本清理执行计划"
echo "=================="
echo ""
echo "⚠️  本脚本仅展示计划，不实际执行删除"
echo "   请审核后再执行实际删除"
echo ""

# 统计当前数量
current_count=$(ls $SCRIPTS/*.py 2>/dev/null | wc -l)
echo "当前脚本总数: $current_count"
echo ""

# ========== 步骤1: 归档能力突破实验 ==========
echo "步骤1: 归档能力突破实验 (15个)"
echo "-------------------------------"
mkdir -p $ARCHIVE/capability-experiments
for i in $(seq -w 1 15); do
    file="$SCRIPTS/capability-breakthrough-exp-${i}.py"
    if [ -f "$file" ]; then
        echo "  归档: capability-breakthrough-exp-${i}.py"
        # mv "$file" $ARCHIVE/capability-experiments/  # 注释掉，仅展示
    fi
done
echo ""

# ========== 步骤2: 删除Moltbook旧版本 ==========
echo "步骤2: 删除Moltbook旧版本 (保留v60,v61,v71)"
echo "--------------------------------------------"
for v in 7 8 21 30 31 32 33 34 40 41 50 51; do
    file="$SCRIPTS/moltbook_social_v${v}.py"
    if [ -f "$file" ]; then
        echo "  删除: moltbook_social_v${v}.py"
        # rm "$file"  # 注释掉，仅展示
    fi
done
echo ""

# ========== 步骤3: 删除临时修复脚本 ==========
echo "步骤3: 删除临时修复脚本 (7个)"
echo "-----------------------------"
temp_scripts=(
    "fix-and-run.py"
    "fix_import_optimized.py"
    "fix_import_standalone.py"
    "fix_import_v2.py"
    "fix_memory_import.py"
    "verify-fix.py"
    "verify_logger.py"
)
for script in "${temp_scripts[@]}"; do
    file="$SCRIPTS/$script"
    if [ -f "$file" ]; then
        echo "  删除: $script"
        # rm "$file"  # 注释掉，仅展示
    fi
done
echo ""

# ========== 步骤4: 删除重复命名 ==========
echo "步骤4: 删除重复命名脚本"
echo "-----------------------"
duplicates=(
    "token_optimizer_v10.py"
    "state-snapshot-drift-v1-backup-20260216.py"
)
for script in "${duplicates[@]}"; do
    file="$SCRIPTS/$script"
    if [ -f "$file" ]; then
        echo "  删除: $script"
        # rm "$file"  # 注释掉，仅展示
    fi
done
echo ""

# ========== 步骤5: 移动测试脚本 ==========
echo "步骤5: 移动测试脚本到 tests/ (13个)"
echo "-----------------------------------"
mkdir -p $SCRIPTS/tests
test_scripts=$(ls $SCRIPTS/test*.py 2>/dev/null)
for file in $test_scripts; do
    basename=$(basename "$file")
    echo "  移动: $basename → tests/"
    # mv "$file" $SCRIPTS/tests/  # 注释掉，仅展示
done
echo ""

# ========== 预估结果 ==========
echo "📊 清理预估结果"
echo "==============="
echo "删除/归档:"
echo "  - 能力突破实验: 15个"
echo "  - Moltbook旧版本: 约8个"
echo "  - 临时修复脚本: 7个"
echo "  - 重复命名: 2个"
echo "  - 测试脚本移动: 13个"
echo ""
echo "预计减少: ~45个脚本 (~14%)"
echo "剩余约: ~270个"
echo ""
echo "⚡ 激进清理目标: 150-170个 (减少50%+)"
echo "   需要更深入分析和用户确认"
