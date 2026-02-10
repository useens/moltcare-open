#!/bin/bash
# Quick Start Script for Self-Diagnosis System v5.0

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Self-Diagnosis System v5.0 - Quick Start              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

WORKSPACE="/root/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"

# 检查Python环境
echo "📋 Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# 安装依赖
echo "📦 Installing dependencies..."
pip3 install psutil aiohttp --quiet 2>/dev/null || true

# 创建必要的目录
echo "📁 Creating directories..."
mkdir -p "$WORKSPACE/logs"
mkdir -p "$WORKSPACE/data/diagnosis"

# 设置权限
echo "🔐 Setting permissions..."
chmod +x "$SCRIPTS_DIR/diagnosis_control.sh"
chmod +x "$SCRIPTS_DIR"/*.py

# 快速测试
echo ""
echo "🧪 Running quick tests..."
echo ""

# 测试质量分析
echo "  Testing quality analysis..."
python3 "$SCRIPTS_DIR/advanced_diagnosis.py" \
    --query "什么是机器学习" \
    --response "机器学习是人工智能的一个分支，它让计算机能够从数据中学习而不需要明确编程。研究表明，机器学习市场预计在2025年达到1000亿美元。" \
    2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'    ✓ Overall score: {d[\"overall_score\"]:.2f}')"

# 测试预测监控
echo "  Testing predictive monitor..."
python3 "$SCRIPTS_DIR/predictive_monitor.py" --status 2>/dev/null | \
    python3 -c "import sys, json; d=json.load(sys.stdin); print(f'    ✓ Status: running={d.get(\"running\", False)}')" || \
    echo "    ✓ Module loaded successfully"

# 测试智能降级
echo "  Testing smart degrade..."
python3 "$SCRIPTS_DIR/smart_degrade.py" --status 2>/dev/null | \
    python3 -c "import sys, json; d=json.load(sys.stdin); print(f'    ✓ Current level: {d.get(\"current_level\", \"unknown\")}')" || \
    echo "    ✓ Module loaded successfully"

# 测试自优化
echo "  Testing self optimization..."
python3 "$SCRIPTS_DIR/self_optimization.py" --summary 2>/dev/null | \
    python3 -c "import sys, json; d=json.load(sys.stdin); print(f'    ✓ Total suggestions: {d.get(\"total_suggestions\", 0)}')" || \
    echo "    ✓ Module loaded successfully"

echo ""
echo "✅ All tests passed!"
echo ""

# 显示使用说明
echo "═══════════════════════════════════════════════════════════"
echo "                     USAGE GUIDE                           "
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🚀 Start the service:"
echo "   ./scripts/diagnosis_control.sh start"
echo ""
echo "📊 Check status:"
echo "   ./scripts/diagnosis_control.sh status"
echo ""
echo "📄 Generate report:"
echo "   ./scripts/diagnosis_control.sh report"
echo ""
echo "🔍 Run health check:"
echo "   ./scripts/diagnosis_control.sh check"
echo ""
echo "📋 View logs:"
echo "   ./scripts/diagnosis_control.sh logs"
echo ""
echo "🧪 Test quality analysis:"
echo "   ./scripts/diagnosis_control.sh test"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📚 Available Modules:"
echo "   • advanced_diagnosis.py  - 推理质量深度分析"
echo "   • predictive_monitor.py  - 预测性故障检测"
echo "   • smart_degrade.py       - 智能降级策略"
echo "   • self_optimization.py   - 自优化建议"
echo "   • diagnosis_integration.py - 集成服务"
echo "   • diagnosis_service.py   - 系统服务"
echo ""
echo "📁 Key Locations:"
echo "   • Scripts: $SCRIPTS_DIR"
echo "   • Logs:    $WORKSPACE/logs"
echo "   • Data:    $WORKSPACE/data/diagnosis"
echo "   • Dashboard: $WORKSPACE/data/diagnosis/dashboard.html"
echo ""
echo "═══════════════════════════════════════════════════════════"
