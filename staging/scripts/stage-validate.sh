#!/bin/bash
# stage-validate.sh - 验证 staging 文件
# 用法: ./stage-validate.sh [文件名，默认全部]

set -e

STAGING_DIR="/root/.openclaw/workspace/staging"
TARGET_FILE="$1"

validate_markdown() {
    local file="$1"
    local name=$(basename "$file")

    echo "📝 验证: $name"

    # 检查文件存在
    if [[ ! -f "$file" ]]; then
        echo "❌ 错误: $name 不存在"
        return 1
    fi

    # 检查是否为空
    if [[ ! -s "$file" ]]; then
        echo "❌ 错误: $name 为空文件"
        return 1
    fi

    # 检查 Markdown 基本语法
    if ! grep -q "^#" "$file" 2>/dev/null; then
        echo "⚠️  警告: $name 可能缺少标题"
    fi

    # YAML 检查 (如果有 frontmatter)
    if head -1 "$file" | grep -q "^---"; then
        # 前后都有 --- 吗？
        local frontmatter_end=$(grep -n "^---" "$file" | sed -n '2p' | cut -d: -f1)
        if [[ -z "$frontmatter_end" ]]; then
            echo "❌ 错误: $name YAML frontmatter 未正确闭合"
            return 1
        fi
    fi

    echo "✅ $name 验证通过"
    return 0
}

echo "=========================================="
echo "🧪 Staging 文件验证"
echo "=========================================="

if [[ -n "$TARGET_FILE" ]]; then
    # 验证单个文件
    FULL_PATH="$STAGING_DIR/$TARGET_FILE"
    if [[ ! -f "$FULL_PATH" ]]; then
        echo "❌ 文件不存在: $TARGET_FILE"
        exit 1
    fi
    validate_markdown "$FULL_PATH"
else
    # 验证所有 .md 文件
    EXIT_CODE=0
    for file in "$STAGING_DIR"/*.md; do
        if [[ -f "$file" ]]; then
            validate_markdown "$file" || EXIT_CODE=1
        fi
    done

    if [[ $EXIT_CODE -eq 0 ]]; then
        echo ""
        echo "✅ 所有文件验证通过"
    else
        echo ""
        echo "❌ 验证发现错误，请修复后再部署"
        exit 1
    fi
fi

echo "=========================================="
