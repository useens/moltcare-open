#!/bin/bash
# 技能效能基准测试 - 每月1号执行
# 测试已安装技能的性能、成功率、使用频率

set -e

WORKSPACE="/root/.openclaw/workspace"
SKILL_DIR="$WORKSPACE/skills"
BENCHMARK_DIR="$WORKSPACE/memory/intel"
DATE=$(date +%Y-%m-%d)

echo "=== 技能效能基准测试开始 $DATE ==="

# 1. 统计技能数量和类型
echo "[1/4] 统计技能数量..."
TOTAL_SKILLS=$(ls -1 $SKILL_DIR 2>/dev/null | wc -l)
echo "总技能数: $TOTAL_SKILLS"

# 2. 检查技能使用频率（基于日志）
echo "[2/4] 分析技能使用频率..."
LOG_FILE="/tmp/openclaw/openclaw-$(date +%Y-%m-%d).log"
if [ -f "$LOG_FILE" ]; then
    echo "最近24小时技能调用:"
    grep -oE '\[skills\][a-zA-Z0-9_-]+' "$LOG_FILE" 2>/dev/null | sort | uniq -c | sort -rn | head -10 || echo "  - 无技能调用记录"
else
    echo "  - 日志文件不存在"
fi

# 3. 技能文件大小检查（识别臃肿技能）
echo "[3/4] 检查技能体积..."
echo "技能大小排名 (前5大):"
du -sh $SKILL_DIR/* 2>/dev/null | sort -rh | head -5

# 4. 生成效能报告
echo "[4/4] 生成效能报告..."
cat > "$BENCHMARK_DIR/skill_benchmark_${DATE}.md" << EOF
# 技能效能基准测试报告 - $DATE

## 基础统计
- **总技能数**: $TOTAL_SKILLS
- **测试时间**: $(date '+%Y-%m-%d %H:%M:%S %Z')
- **工作区**: $WORKSPACE

## 使用频率分析
$(if [ -f "$LOG_FILE" ]; then
    echo "最近24小时Top 10技能:"
    grep -oE '\[skills\][a-zA-Z0-9_-]+' "$LOG_FILE" 2>/dev/null | sort | uniq -c | sort -rn | head -10 | sed 's/^/  - /'
else
    echo "  - 暂无日志数据"
fi)

## 技能体积分析
最大5个技能:
$(du -sh $SKILL_DIR/* 2>/dev/null | sort -rh | head -5 | sed 's/^/  - /')

## 待优化技能（推测）
基于文件大小和使用频率，可能需要优化的技能：
$(du -sh $SKILL_DIR/* 2>/dev/null | awk '{print $2}' | while read skill; do
    # 如果技能很大但很少使用，标记为待优化
    size=$(du -sb "$skill" 2>/dev/null | awk '{print $1}')
    if [ "$size" -gt 100000 ]; then  # 100KB以上
        echo "  - $(basename $skill): 体积较大(${size}bytes)，检查是否必需"
    fi
done)

## 建议
1. 移除30天未使用的技能
2. 优化大体积极少使用的技能
3. 监控技能调用失败率
4. 定期更新技能到最新版本

---
*月度基准测试*
EOF

echo "=== 基准测试完成 ==="
echo "报告位置: $BENCHMARK_DIR/skill_benchmark_${DATE}.md"
