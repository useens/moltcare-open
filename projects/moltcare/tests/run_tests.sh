#!/bin/bash
# 测试执行脚本 - 用于本地测试

set -e

echo "🧪 Moltcare 测试框架"
echo "===================="

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$(dirname "$0")/.."

echo ""
echo "📦 安装依赖..."
pip install -e . -q
pip install pytest pytest-cov pytest-xdist -q

echo ""
echo "🔍 运行单元测试..."
pytest tests/unit -v --cov=moltcare --cov-report=term-missing || {
    echo -e "${RED}❌ 单元测试失败${NC}"
    exit 1
}

echo ""
echo "🔗 运行集成测试..."
pytest tests/integration -v --cov=moltcare --cov-report=term-missing --cov-append || {
    echo -e "${RED}❌ 集成测试失败${NC}"
    exit 1
}

echo ""
echo "📊 检查CLI覆盖率..."
pytest tests/unit/test_cli.py -v --cov=moltcare.cli --cov-report=term-missing --cov-fail-under=100 || {
    echo -e "${RED}❌ CLI覆盖率未达到100%${NC}"
    exit 1
}

echo ""
echo "✅ 测试验证示例配置..."
moltcare diagnose -w tests/examples/basic-agent || true
moltcare diagnose -w tests/examples/advanced-agent || true

echo ""
echo -e "${GREEN}✅ 所有测试通过!${NC}"
echo ""
echo "📈 生成覆盖率报告..."
pytest --cov=moltcare --cov-report=html --cov-report=xml

echo ""
echo "📁 覆盖率报告: htmlcov/index.html"
