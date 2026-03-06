#!/bin/bash
# 神经中枢执行全面审计，结合Nanobot发现

echo "🧠 神经中枢执行全面脚本审计"
echo "============================="
echo ""

cd /root/.openclaw/workspace

# 创建报告目录
mkdir -p reports

echo "📊 正在收集数据..."
echo ""

# 1. 脚本总数统计
echo "1️⃣ 脚本总数统计"
echo "----------------"
PY_COUNT=$(find scripts -name '*.py' -type f | wc -l)
SH_COUNT=$(find scripts -name '*.sh' -type f | wc -l)
ARCHIVED_COUNT=$(find scripts/.archive -name '*.py' -type f 2>/dev/null | wc -l)
TESTS_COUNT=$(ls scripts/tests/*.py 2>/dev/null | wc -l)

echo "  Python脚本: $PY_COUNT 个"
echo "  Shell脚本: $SH_COUNT 个"
echo "  已归档: $ARCHIVED_COUNT 个"
echo "  测试脚本: $TESTS_COUNT 个"
echo "  总计: $((PY_COUNT + SH_COUNT)) 个脚本文件"
echo ""

# 2. 活跃状态分析
echo "2️⃣ 活跃状态分析"
echo "----------------"
ACTIVE_30D=$(find scripts -name '*.py' -type f -atime -30 | wc -l)
ACTIVE_7D=$(find scripts -name '*.py' -type f -atime -7 | wc -l)

echo "  30天内访问: $ACTIVE_30D 个"
echo "  7天内访问: $ACTIVE_7D 个"
echo "  超过30天未访问: $((PY_COUNT - ACTIVE_30D)) 个"
echo ""

# 3. Cron引用检查
echo "3️⃣ Cron引用检查"
echo "----------------"
CRON_SCRIPTS=$(crontab -l 2>/dev/null | grep -oE '[a-zA-Z0-9_-]+\.(py|sh)' | sort -u | wc -l)
echo "  Cron引用的脚本: $CRON_SCRIPTS 个"
crontab -l 2>/dev/null | grep -oE '[a-zA-Z0-9_-]+\.(py|sh)' | sort -u | head -10 | sed 's/^/    /'
echo ""

# 4. 运行中的进程
echo "4️⃣ 运行中的Python进程"
echo "---------------------"
RUNNING_SCRIPTS=$(ps aux | grep python | grep -v grep | awk '{print $NF}' | grep -E '\.py$' | sort -u | wc -l)
echo "  运行中的脚本: $RUNNING_SCRIPTS 个"
ps aux | grep python | grep -v grep | awk '{print $NF}' | grep -E '\.py$' | sort -u | head -10 | sed 's/^/    /'
echo ""

# 5. 代码行数统计
echo "5️⃣ 代码行数统计"
echo "----------------"
TOTAL_LINES=$(find scripts -name '*.py' -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
echo "  Python脚本总行数: ${TOTAL_LINES:-0} 行"
echo "  平均每个脚本: $((${TOTAL_LINES:-0} / ${PY_COUNT:-1})) 行"
echo ""

# 6. 最大脚本
echo "6️⃣ 最大脚本 (前10)"
echo "------------------"
ls -lS scripts/*.py 2>/dev/null | head -10 | awk '{printf "  %8s  %s\n", $5, $NF}'
echo ""

# 7. 空文件检查
echo "7️⃣ 空文件检查"
echo "--------------"
EMPTY_FILES=$(find scripts -name '*.py' -size 0 2>/dev/null | wc -l)
echo "  空文件: $EMPTY_FILES 个"
find scripts -name '*.py' -size 0 2>/dev/null | sed 's/^/    /'
echo ""

# 8. 磁盘使用
echo "8️⃣ 磁盘使用"
echo "------------"
df -h /root/.openclaw/workspace | tail -1 | awk '{printf "  已使用: %s / %s (可用: %s)\n", $3, $2, $4}'
echo ""

# 生成报告
echo "📝 生成审计报告..."
cat > reports/nanobot-full-audit-report.json << EOF
{
  "audit_time": "$(date -Iseconds)",
  "auditor": "neural_hub",
  "summary": {
    "python_scripts": $PY_COUNT,
    "shell_scripts": $SH_COUNT,
    "archived_scripts": $ARCHIVED_COUNT,
    "test_scripts": $TESTS_COUNT,
    "total_scripts": $((PY_COUNT + SH_COUNT)),
    "active_30d": $ACTIVE_30D,
    "active_7d": $ACTIVE_7D,
    "inactive": $((PY_COUNT - ACTIVE_30D)),
    "cron_referenced": $CRON_SCRIPTS,
    "running": $RUNNING_SCRIPTS,
    "total_lines": ${TOTAL_LINES:-0},
    "empty_files": $EMPTY_FILES
  },
  "recommendations": [
    "继续归档旧版本脚本",
    "清理超过30天未访问的脚本(已清理)",
    "合并功能重复的脚本",
    "将测试脚本保持在tests/目录"
  ]
}
EOF

echo "✅ 审计报告已保存: reports/nanobot-full-audit-report.json"
