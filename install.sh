#!/bin/bash
# MoltCare Foundation Pack - 一键安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/master/install.sh | bash

set -e

REPO_URL="https://github.com/useens/moltcare-open"

# 默认安装到 OpenClaw workspace 根目录
TARGET_DIR="${1:-$HOME/.openclaw/workspace}"

echo "🦞 MoltCare Foundation Pack v2.3.3"
echo ""

# 确认目标目录
if [ ! -d "$TARGET_DIR" ]; then
    echo "📁 创建工作目录: $TARGET_DIR"
    mkdir -p "$TARGET_DIR"
fi

echo "🎯 安装目标: $TARGET_DIR"
echo ""

# 下载模板
echo "📥 下载模板..."
TMP_DIR=$(mktemp -d)
if command -v curl &>/dev/null; then
    curl -fsSL "$REPO_URL/archive/refs/heads/master.tar.gz" | tar -xz -C "$TMP_DIR"
elif command -v wget &>/dev/null; then
    wget -q "$REPO_URL/archive/refs/heads/master.tar.gz" -O - | tar -xz -C "$TMP_DIR"
else
    echo "❌ 需要 curl 或 wget"
    exit 1
fi

REPO_TMP="$TMP_DIR/moltcare-open-master"

# 安装核心文件到根目录（Agent 必须识别的文件）
echo ""
echo "📋 安装核心配置到根目录..."
cp "$REPO_TMP/templates/core/SOUL.md" "$TARGET_DIR/"
cp "$REPO_TMP/templates/core/AGENTS.md" "$TARGET_DIR/"
cp "$REPO_TMP/templates/core/USER.md" "$TARGET_DIR/"
echo "  ✅ SOUL.md"
echo "  ✅ AGENTS.md"
echo "  ✅ USER.md"

# 安装系统文件到根目录
echo ""
echo "📋 安装系统文件..."
cp "$REPO_TMP/templates/system/MEMORY.md" "$TARGET_DIR/"
cp "$REPO_TMP/templates/system/HEARTBEAT.md" "$TARGET_DIR/"
echo "  ✅ MEMORY.md"
echo "  ✅ HEARTBEAT.md"

# 安装工具文件到根目录
echo ""
echo "📋 安装工具模板..."
for file in "$REPO_TMP/tools/"*.md; do
    if [ -f "$file" ]; then
        cp "$file" "$TARGET_DIR/"
        echo "  ✅ $(basename "$file")"
    fi
done

# 创建 memory/ 子目录并安装记忆工具
echo ""
echo "📋 安装记忆工具到 memory/ 目录..."
mkdir -p "$TARGET_DIR/memory"
for file in "$REPO_TMP/templates/memory/"*.md; do
    if [ -f "$file" ]; then
        cp "$file" "$TARGET_DIR/memory/"
        echo "  ✅ memory/$(basename "$file")"
    fi
done

# 可选：安装文档
echo ""
echo "📋 安装集成文档（可选）..."
mkdir -p "$TARGET_DIR/docs"
for file in "$REPO_TMP/docs/"*.md; do
    if [ -f "$file" ]; then
        cp "$file" "$TARGET_DIR/docs/"
        echo "  ✅ docs/$(basename "$file")"
    fi
done

# 清理临时文件
rm -rf "$TMP_DIR"

echo ""
echo "================================"
echo "✅ 安装完成！"
echo "================================"
echo ""
echo "已安装到: $TARGET_DIR"
echo ""
echo "核心文件（根目录）:"
echo "  📄 SOUL.md       - Agent 灵魂定义"
echo "  📄 AGENTS.md     - 操作手册"
echo "  📄 USER.md       - 用户画像"
echo "  📄 MEMORY.md     - 记忆系统"
echo "  📄 HEARTBEAT.md  - 状态报告模板"
echo ""
echo "子目录:"
echo "  📁 memory/       - 学习债务、约束、偏好"
echo "  📁 docs/         - 集成指南（可选）"
echo ""
echo "下一步:"
echo "  1. 📝 运行配置向导（推荐）"
echo "     $TARGET_DIR/scripts/onboarding.sh"
echo ""
echo "  2. ✏️  或手动编辑 USER.md"
echo "     nano $TARGET_DIR/USER.md"
echo ""
echo "  3. 🔄 重启 OpenClaw Agent 加载新配置"
echo ""
echo "📖 详细说明: https://github.com/useens/moltcare-open#readme"
echo ""

# 询问是否运行配置向导
if [ -t 0 ]; then
    echo ""
    read -t 10 -p "是否现在运行配置向导? (y/N, 10秒后自动跳过) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        "$TARGET_DIR/scripts/onboarding.sh"
    fi
fi
