#!/bin/bash
# 安装脚本 - 本地记忆系统

set -e

echo "🧠 本地记忆系统安装脚本"
echo "======================="
echo ""

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📋 Python 版本: $python_version"

# 安装依赖
echo ""
echo "📦 正在安装依赖..."
pip install -r requirements.txt

# 创建命令别名
echo ""
echo "🔗 创建命令别名..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 添加到 .bashrc (如果未添加)
ALIAS_CMD="alias local-memory='python3 $SCRIPT_DIR/local_memory.py'"
if ! grep -q "$ALIAS_CMD" ~/.bashrc 2>/dev/null; then
    echo "$ALIAS_CMD" >> ~/.bashrc
    echo "✅ 已添加 alias 到 ~/.bashrc"
    echo "   请运行: source ~/.bashrc"
else
    echo "✅ alias 已存在"
fi

echo ""
echo "🎉 安装完成!"
echo ""
echo "使用说明:"
echo "  初始化:     local-memory init"
echo "  索引文件:   local-memory index <file>"
echo "  搜索:       local-memory search <query>"
echo "  列出文档:   local-memory list"
echo "  查看统计:   local-memory stats"
echo ""
