#!/bin/bash
# =============================================================================
# 向量记忆系统初始化脚本
# 夜间进化第2轮 - 自动修复向量存储
# =============================================================================

set -e

echo "🧠 向量记忆系统初始化"
echo "时间: $(date)"
echo ""

WORKSPACE="$HOME/.openclaw/workspace"
cd "$WORKSPACE"

# 检查Python环境
echo "--- 检查Python环境 ---"
python3 --version

# 初始化向量存储
echo ""
echo "--- 初始化向量存储 ---"
python3 -c "
import sys
sys.path.insert(0, '.')
from core.vector_memory.vector_store import VectorStore
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

store = VectorStore('data/vector_memory')
print('✅ 向量存储初始化成功')
"

# 创建必要的目录
echo ""
echo "--- 创建必要的目录 ---"
mkdir -p data/vector_memory
mkdir -p memory/vector-store
mkdir -p logs/vector_memory

echo "✅ 目录创建完成"

# 测试向量存储
echo ""
echo "--- 测试向量存储 ---"
python3 -c "
import sys
sys.path.insert(0, '.')
from core.vector_memory.vector_store import VectorStore

store = VectorStore('data/vector_memory')

# 测试写入
test_id = store.add('夜间进化第2轮初始化测试', {'source': 'init-script', 'type': 'test'})
print(f'✅ 测试写入成功: {test_id}')

# 测试检索
results = store.search('初始化', limit=5)
print(f'✅ 测试检索成功: 找到 {len(results)} 条结果')

# 显示统计
stats = store.get_stats()
print(f'📊 当前记录数: {stats.get(\"total_records\", 0)}')
"

echo ""
echo "✅ 向量记忆系统初始化完成"
echo "时间: $(date)"
