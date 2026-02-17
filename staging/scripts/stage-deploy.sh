#!/bin/bash
# stage-deploy.sh - 部署 staging 文件到生产环境
# 用法: ./stage-deploy.sh [文件名，默认全部]

set -e

STAGING_DIR="/root/.openclaw/workspace/staging"
WORKSPACE_DIR="/root/.openclaw/workspace"
BACKUP_DIR="$STAGING_DIR/backups/$(date +%Y%m%d_%H%M%S)"

TARGET_FILE="$1"

deploy_file() {
    local filename="$1"
    local source="$STAGING_DIR/$filename"
    local target="$WORKSPACE_DIR/$filename"

    # 检查源文件存在
    if [[ ! -f "$source" ]]; then
        echo "❌ 源文件不存在: $filename"
        return 1
    fi

    # 创建备份
    if [[ -f "$target" ]]; then
        mkdir -p "$BACKUP_DIR"
        cp "$target" "$BACKUP_DIR/"
        echo "📦 备份: $filename → backups/$(basename $BACKUP_DIR)/"
    fi

    # 部署
    cp "$source" "$target"
    echo "✅ 部署: $filename"

    return 0
}

echo "=========================================="
echo "🚀 部署 Staging → Production"
echo "=========================================="

# 先验证
if [[ -n "$TARGET_FILE" ]]; then
    "$STAGING_DIR/scripts/stage-validate.sh" "$TARGET_FILE" || exit 1
else
    "$STAGING_DIR/scripts/stage-validate.sh" || exit 1
fi

echo ""
echo "开始部署..."
echo ""

mkdir -p "$BACKUP_DIR"

if [[ -n "$TARGET_FILE" ]]; then
    deploy_file "$TARGET_FILE" || exit 1
else
    # 部署所有文件
    EXIT_CODE=0
    for file in "$STAGING_DIR"/*.md; do
        if [[ -f "$file" ]]; then
            filename=$(basename "$file")
            # 跳过 README.md (如果存在)
            [[ "$filename" == "README.md" ]] && continue
            deploy_file "$filename" || EXIT_CODE=1
        fi
    done

    if [[ $EXIT_CODE -ne 0 ]]; then
        echo ""
        echo "⚠️ 部分文件部署失败"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "✅ 部署完成"
echo "📁 备份位置: $BACKUP_DIR"
echo "=========================================="
echo ""
echo "🧪 请立即验证修改效果："
echo "   - 检查 OpenClaw 是否正常响应"
echo "   - 测试修改的功能是否生效"
echo ""
echo "🔄 如需回滚: ./stage-rollback.sh [$(basename $BACKUP_DIR)]"
