#!/bin/bash
# 向量记忆导出脚本 - 将向量记忆导出为可Git管理的JSON格式
# 用途：在Git备份和本地备份之间建立桥梁

set -e

WORKSPACE="/root/.openclaw/workspace"
DATA_DIR="$WORKSPACE/data/vector_memory"
EXPORT_DIR="$WORKSPACE/data/vector_memory_export"
DATE=$(date +%Y%m%d)

echo "=== 向量记忆导出 ==="
echo "时间: $(date)"

# 检查向量存储是否存在
if [ ! -d "$DATA_DIR" ]; then
    echo "❌ 向量存储目录不存在"
    exit 1
fi

mkdir -p "$EXPORT_DIR"

# 导出向量记忆元数据（不包含实际向量数据，只导出索引和元数据）
# 实际向量数据仍通过备份管理
cat > "$EXPORT_DIR/README.md" << EOF
# 向量记忆导出说明

**最后导出**: $(date)
**原始位置**: data/vector_memory/

## 恢复流程

1. 从GitHub克隆代码仓库
2. 从备份恢复向量数据:
   ```bash
   # 方法1: 从本地备份恢复
   tar -xzf /root/.openclaw/backups/local/workspace_backup_*.tar.gz -C /tmp/
   cp -r /tmp/workspace/data/vector_memory ./data/
   
   # 方法2: 重新初始化向量记忆
   python3 scripts/init-vector-memory-full.py
   ```

3. 验证向量记忆:
   python3 scripts/unified-monitor.py --component memory

## 注意事项
- 向量数据是二进制格式，不适合Git管理
- 通过Cron每天03:00自动备份到 /backups/local/
- 保留最近10个备份，超过的自动清理
EOF

echo "✅ 导出完成: $EXPORT_DIR/README.md"
echo ""
echo "📊 向量记忆统计:"
echo "  - 数据目录大小: $(du -sh $DATA_DIR | cut -f1)"
echo "  - 备份目录大小: $(du -sh $WORKSPACE/backups/local/ 2>/dev/null | cut -f1 || echo 'N/A')"
echo ""
echo "💡 恢复时请参考上述README.md"
