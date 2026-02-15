#!/bin/bash
# 森森复活脚本 - 从GitHub克隆后恢复完整系统
# 用途: 在新环境恢复代码+数据+记忆

set -e

REPO_URL="https://github.com/useens/linlin-backup.git"
WORKSPACE="/root/.openclaw/workspace"
BACKUP_DIR="/root/.openclaw/backups"

echo "🌲 森森复活脚本"
echo "=============="
echo ""

# 检查是否已克隆
if [ ! -d "$WORKSPACE/.git" ]; then
    echo "1. 克隆代码仓库..."
    mkdir -p $(dirname $WORKSPACE)
    git clone $REPO_URL $WORKSPACE
    cd $WORKSPACE
else
    echo "1. 使用现有仓库"
    cd $WORKSPACE
fi

echo ""
echo "2. 检查备份可用性..."

# 优先从本地备份恢复数据
if [ -d "$BACKUP_DIR/local" ] && [ "$(ls -A $BACKUP_DIR/local/*.tar.gz 2>/dev/null)" ]; then
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/local/*.tar.gz | head -1)
    echo "   ✅ 找到本地备份: $LATEST_BACKUP"
    echo ""
    echo "3. 从本地备份恢复数据..."
    tar -xzf "$LATEST_BACKUP" -C /tmp/ workspace/data/ 2>/dev/null || true
    if [ -d "/tmp/workspace/data" ]; then
        cp -r /tmp/workspace/data/* "$WORKSPACE/data/" 2>/dev/null || true
        rm -rf /tmp/workspace
        echo "   ✅ 数据恢复完成"
    fi
else
    echo "   ⚠️ 未找到本地备份"
    echo ""
    echo "3. 初始化新数据..."
    if [ -f "scripts/init-vector-memory-full.py" ]; then
        python3 scripts/init-vector-memory-full.py 2>/dev/null || echo "   ⚠️ 向量记忆初始化失败，将自动创建"
    fi
    echo "   ✅ 新数据初始化完成"
fi

echo ""
echo "4. 验证系统..."
cd $WORKSPACE

# 检查关键目录
for dir in data memory logs reports; do
    if [ -d "$dir" ]; then
        echo "   ✅ $dir 目录正常"
    else
        mkdir -p "$dir"
        echo "   📝 创建 $dir 目录"
    fi
done

echo ""
echo "5. 系统状态检查..."

# 检查向量记忆
if [ -d "data/vector_memory" ] && [ "$(ls -A data/vector_memory 2>/dev/null)" ]; then
    VECTOR_SIZE=$(du -sh data/vector_memory 2>/dev/null | cut -f1)
    echo "   ✅ 向量记忆: $VECTOR_SIZE"
else
    echo "   ⚠️ 向量记忆为空，将在运行时自动重建"
fi

# 检查Cron配置
echo ""
echo "6. 恢复Cron配置..."
if [ -f "config/cron-tasks.json" ]; then
    echo "   ✅ Cron配置文件存在"
    echo "   💡 请手动导入: openclaw cron import config/cron-tasks.json"
else
    echo "   ⚠️ Cron配置文件不存在"
fi

echo ""
echo "=============="
echo "🎉 复活完成!"
echo ""
echo "📋 后续步骤:"
echo "   1. 检查 .env 文件（如需要恢复凭证）"
echo "   2. 运行: openclaw cron import config/cron-tasks.json"
echo "   3. 运行: python3 scripts/unified-monitor.py --fix"
echo ""
echo "🌲 森森已就绪"
