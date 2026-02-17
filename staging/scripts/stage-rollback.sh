#!/bin/bash
# stage-rollback.sh - 回滚到之前的版本
# 用法: ./stage-rollback.sh [备份ID，默认最新]

BACKUPS_DIR="/root/.openclaw/workspace/staging/backups"
WORKSPACE_DIR="/root/.openclaw/workspace"

BACKUP_ID="$1"

list_backups() {
    echo "📁 可用备份:"
    ls -1 -t "$BACKUPS_DIR"/ 2>/dev/null | head -10 | nl
}

if [[ ! -d "$BACKUPS_DIR" ]]; then
    echo "❌ 备份目录不存在"
    exit 1
fi

if [[ -z "$BACKUP_ID" ]]; then
    # 使用最新的备份
    BACKUP_FOLDER=$(ls -1 -t "$BACKUPS_DIR"/ 2>/dev/null | head -1)
    if [[ -z "$BACKUP_FOLDER" ]]; then
        echo "❌ 没有找到备份"
        exit 1
    fi
else
    # 支持两种输入: 数字索引 或 完整备份名
    if [[ "$BACKUP_ID" =~ ^[0-9]+$ ]]; then
        # 数字索引
        BACKUP_FOLDER=$(ls -1 -t "$BACKUPS_DIR"/ 2>/dev/null | sed -n "${BACKUP_ID}p")
        if [[ -z "$BACKUP_FOLDER" ]]; then
            echo "❌ 备份 #$BACKUP_ID 不存在"
            list_backups
            exit 1
        fi
    else
        # 完整备份名
        BACKUP_FOLDER="$BACKUP_ID"
        if [[ ! -d "$BACKUPS_DIR/$BACKUP_FOLDER" ]]; then
            echo "❌ 备份 $BACKUP_ID 不存在"
            list_backups
            exit 1
        fi
    fi
fi

BACKUP_PATH="$BACKUPS_DIR/$BACKUP_FOLDER"

echo "=========================================="
echo "🔄 回滚到备份: $BACKUP_FOLDER"
echo "=========================================="

# 确认
read -p "确认回滚? 这将覆盖当前文件 (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 执行回滚
ROLLBACK_COUNT=0
for file in "$BACKUP_PATH"/*.md; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        cp "$file" "$WORKSPACE_DIR/$filename"
        echo "✅ 回滚: $filename"
        ((ROLLBACK_COUNT++))
    fi
done

if [[ $ROLLBACK_COUNT -eq 0 ]]; then
    echo "❌ 备份中没有可回滚的文件"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 回滚完成"
echo "📁 回滚的备份: $BACKUP_FOLDER"
echo "📊 恢复文件数: $ROLLBACK_COUNT"
echo "=========================================="
echo ""
echo "⚠️ 请验证系统是否恢复正常"
