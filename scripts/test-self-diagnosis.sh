#!/bin/bash
# 林林 v5.0 自我诊断系统 - 测试脚本

echo "=============================================="
echo "林林 v5.0 自我诊断系统 - 部署测试"
echo "=============================================="
echo ""

WORKSPACE="/root/.openclaw/workspace"

cd "$WORKSPACE"

# 1. 检查文件
echo "[1/5] 检查文件..."
for file in scripts/self-diagnosis.py scripts/auto-heal.py scripts/health-monitor-v5.py docs/self-diagnosis.md; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file 缺失!"
        exit 1
    fi
done

# 2. 检查权限
echo ""
echo "[2/5] 检查执行权限..."
for script in scripts/self-diagnosis.py scripts/auto-heal.py scripts/health-monitor-v5.py; do
    if [ -x "$script" ]; then
        echo "  ✓ $script 可执行"
    else
        echo "  ✗ $script 无执行权限"
    fi
done

# 3. 测试诊断脚本
echo ""
echo "[3/5] 测试诊断脚本..."
python3 scripts/self-diagnosis.py --json > /tmp/test_diagnosis.json 2>&1
if [ $? -eq 0 ] && [ -s /tmp/test_diagnosis.json ]; then
    echo "  ✓ 诊断脚本运行成功"
    STATUS=$(python3 -c "import json; print(json.load(open('/tmp/test_diagnosis.json'))['overall_status'])" 2>/dev/null || echo "unknown")
    SCORE=$(python3 -c "import json; print(json.load(open('/tmp/test_diagnosis.json'))['overall_score'])" 2>/dev/null || echo "0")
    echo "    状态: $STATUS, 分数: $SCORE"
else
    echo "  ⚠ 诊断脚本可能有问题，检查日志"
fi

# 4. 检查日志目录
echo ""
echo "[4/5] 检查日志目录..."
for dir in logs data; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir/ 目录存在"
    else
        echo "  ✗ $dir/ 目录缺失"
    fi
done

# 5. 检查crontab
echo ""
echo "[5/5] 检查crontab配置..."
if crontab -l | grep -q "health-monitor-v5.py"; then
    echo "  ✓ crontab任务已配置"
    echo "    任务: $(crontab -l | grep "health-monitor-v5.py")"
else
    echo "  ✗ crontab任务未配置"
fi

echo ""
echo "=============================================="
echo "测试完成!"
echo "=============================================="
echo ""
echo "系统状态:"
python3 scripts/self-diagnosis.py --json 2>/dev/null | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(f\"  总体状态: {d['overall_status']}\")
    print(f\"  健康分数: {d['overall_score']:.1f}/100\")
    print(f\"  检查项目: {len(d['checks'])} 项\")
    warnings = [c for c in d['checks'] if c['status'] == 'warning']
    critical = [c for c in d['checks'] if c['status'] == 'critical']
    if critical:
        print(f\"  ⚠️  严重问题: {len(critical)} 项\")
    if warnings:
        print(f\"  ⚠️  警告问题: {len(warnings)} 项\")
except:
    print('  无法获取系统状态')
"
echo ""
echo "使用说明:"
echo "  - 手动诊断: python3 scripts/self-diagnosis.py"
echo "  - 手动修复: python3 scripts/auto-heal.py"
echo "  - 查看日志: tail -f logs/health-monitor-v5.log"
echo "  - 查看文档: docs/self-diagnosis.md"
echo ""
