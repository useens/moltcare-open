#!/bin/bash
# Moltcare 一键安装脚本

set -e

echo "🚀 安装 Moltcare..."

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.10+ 是必需的，当前版本: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python 版本检查通过"

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装"
    exit 1
fi

echo "✓ pip3 检查通过"

# 安装 Moltcare
echo "📦 安装 Moltcare..."
pip3 install -e .

# 验证安装
if command -v moltcare &> /dev/null; then
    echo ""
    echo "✅ Moltcare 安装成功!"
    echo ""
    moltcare --version
    echo ""
    echo "开始使用:"
    echo "  moltcare init      # 初始化 Agent 配置"
    echo "  moltcare --help    # 查看帮助"
else
    echo "⚠️  安装完成，但命令未找到"
    echo "请确保 pip 安装目录在 PATH 中"
fi
