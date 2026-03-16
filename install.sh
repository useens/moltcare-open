#!/bin/bash
# MoltCare Foundation Pack - 一键安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/master/install.sh | bash

set -e

REPO_URL="https://github.com/useens/moltcare-open"

# 默认安装到 OpenClaw workspace 根目录
TARGET_DIR="${1:-$HOME/.openclaw/workspace}"

echo "🦞 MoltCare Foundation Pack v3.2"
echo ""

# 确认目标目录
if [ ! -d "$TARGET_DIR" ]; then
    echo "📁 创建工作目录: $TARGET_DIR"
    mkdir -p "$TARGET_DIR"
fi

echo "🎯 安装目标: $TARGET_DIR"
echo ""

# 下载模板
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

# 安装 CORE 文件（OpenClaw 自动加载）
echo ""
echo "📋 安装 CORE 配置（OpenClaw 自动加载）..."
cp "$REPO_TMP/templates/core/AGENTS.md" "$TARGET_DIR/"
cp "$REPO_TMP/templates/core/SOUL.md" "$TARGET_DIR/"
cp "$REPO_TMP/templates/core/USER.md" "$TARGET_DIR/"
cp "$REPO_TMP/templates/system/MEMORY.md" "$TARGET_DIR/"
echo "  ✅ AGENTS.md    - 操作手册"
echo "  ✅ SOUL.md      - Agent 灵魂定义"
echo "  ✅ USER.md      - 用户画像"
echo "  ✅ MEMORY.md    - 长期记忆"

# 安装 OPTIONAL 文件（存在则加载）
echo ""
echo "📋 安装 OPTIONAL 配置（存在则加载）..."
cp "$REPO_TMP/templates/core/IDENTITY.md" "$TARGET_DIR/" 2>/dev/null || echo "  ⚠️  IDENTITY.md 未找到"
cp "$REPO_TMP/templates/core/TOOLS.md" "$TARGET_DIR/" 2>/dev/null || echo "  ⚠️  TOOLS.md 未找到"
cp "$REPO_TMP/templates/system/HEARTBEAT.md" "$TARGET_DIR/" 2>/dev/null || echo "  ⚠️  HEARTBEAT.md 未找到"
cp "$REPO_TMP/templates/core/TOKEN_AUDIT.md" "$TARGET_DIR/" 2>/dev/null || echo "  ⚠️  TOKEN_AUDIT.md 未找到"
cp "$REPO_TMP/templates/core/CONFIG_CHECKLIST.md" "$TARGET_DIR/" 2>/dev/null || echo "  ⚠️  CONFIG_CHECKLIST.md 未找到"
echo "  ✅ IDENTITY.md  - Agent 身份"
echo "  ✅ TOOLS.md     - 环境工具"
echo "  ✅ HEARTBEAT.md - 状态检查"
echo "  ✅ TOKEN_AUDIT.md - Token 审查配置"
echo "  ✅ CONFIG_CHECKLIST.md - 配置检查清单"

# 创建 memory/ 子目录并安装记忆工具（按需读取）
echo ""
echo "📋 安装 MEMORY 工具（按需读取）..."
mkdir -p "$TARGET_DIR/memory"
cp "$REPO_TMP/templates/memory/learning-debt.md" "$TARGET_DIR/memory/" 2>/dev/null || echo "  ⚠️  learning-debt.md 未找到"
cp "$REPO_TMP/templates/memory/constraints.md" "$TARGET_DIR/memory/" 2>/dev/null || echo "  ⚠️  constraints.md 未找到"
cp "$REPO_TMP/templates/memory/preferences.md" "$TARGET_DIR/memory/" 2>/dev/null || echo "  ⚠️  preferences.md 未找到"
cp "$REPO_TMP/templates/memory/token-audit-template.md" "$TARGET_DIR/memory/" 2>/dev/null || echo "  ⚠️  token-audit-template.md 未找到"
echo "  ✅ memory/learning-debt.md"
echo "  ✅ memory/constraints.md"
echo "  ✅ memory/preferences.md"
echo "  ✅ memory/token-audit-template.md"

# 可选：安装文档
echo ""
echo "📋 安装文档（可选，不自动加载）..."
mkdir -p "$TARGET_DIR/docs"
for file in "$REPO_TMP/docs/"*.md; do
    if [ -f "$file" ]; then
        cp "$file" "$TARGET_DIR/docs/"
        echo "  ✅ docs/$(basename "$file")"
    fi
done

# 清理临时文件
rm -rf "$TMP_DIR"

# 创建今日记忆文件
TODAY=$(date +%Y-%m-%d)
if [ ! -f "$TARGET_DIR/memory/${TODAY}.md" ]; then
    echo "# ${TODAY} Memory Flush" > "$TARGET_DIR/memory/${TODAY}.md"
    echo "  ✅ memory/${TODAY}.md (今日记忆)"
fi

# 配置每周 Token 审查 cron
echo ""
echo "⏰ 配置每周 Token 审查..."
if ! crontab -l 2>/dev/null | grep -q "检查token优化"; then
    (crontab -l 2>/dev/null; echo "0 3 * * 1 cd $TARGET_DIR && echo '检查token优化' >> $TARGET_DIR/.audit-trigger 2>&1") | crontab -
    echo "  ✅ 已配置每周一 03:00 自动执行 Token 审查"
else
    echo "  ⏭️  Token 审查已配置，跳过"
fi

echo ""
echo "================================"
echo "✅ 安装完成！"
echo "================================"
echo ""
echo "已安装到: $TARGET_DIR"
echo ""
echo "📁 CORE 文件（自动加载）:"
echo "   AGENTS.md, SOUL.md, USER.md, MEMORY.md"
echo ""
echo "📁 OPTIONAL 文件（存在则加载）:"
echo "   IDENTITY.md, TOOLS.md, HEARTBEAT.md, TOKEN_AUDIT.md"
echo ""
echo "⚠️  重要: 安装后必读 CONFIG_CHECKLIST.md"
echo "   cat ~/.openclaw/workspace/CONFIG_CHECKLIST.md"
echo ""
echo "📁 MEMORY 模板（按需读取）:"
echo "   memory/learning-debt.md"
echo "   memory/constraints.md"
echo "   memory/preferences.md"
echo "   memory/token-audit-template.md"
echo ""
echo "⏰ 自动化任务:"
echo "   每周 Token 审查: 周一 03:00 (cron)"
echo ""
echo "📖 参考文档（不自动加载）:"
echo "   skill/assets/BEST_PRACTICES.md - 效率最佳实践"
echo ""
echo "下一步:"
echo "  1. 📝 编辑 USER.md 配置用户画像"
echo "     nano $TARGET_DIR/USER.md"
echo ""
echo "  2. 🔄 重启 OpenClaw Agent 加载新配置"
echo ""
echo "📖 详细说明: https://github.com/useens/moltcare-open#readme"
echo ""
