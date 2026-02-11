#!/bin/bash
# 记忆系统启动恢复脚本
# 在系统启动时运行，确保所有组件就绪

echo "🌱 记忆系统启动恢复..."

cd /root/.openclaw/workspace

# 1. 检查向量记忆
if [ ! -f "memory/vector/memory_vectors.pkl" ]; then
    echo "❌ 向量记忆文件缺失，需要重建"
    # 从长期记忆重建
    if [ -f "memory/long_term_memories.json" ]; then
        echo "🔄 从长期记忆重建向量..."
        python3 scripts/memory-system/enhanced_layered_memory.py
    fi
fi

# 2. 检查长期记忆
if [ ! -f "memory/long_term_memories.json" ]; then
    echo "🔄 初始化长期记忆..."
    python3 scripts/memory-system/enhanced_layered_memory.py
fi

# 3. 检查关联图谱
if [ ! -f "memory/associations/memory_graph.json" ]; then
    echo "🔄 初始化关联图谱..."
    python3 scripts/memory-system/enhanced_layered_memory.py
fi

# 4. 检查主动回忆系统
if [ ! -f "memory/proactive/patterns.json" ]; then
    echo "🔄 初始化主动回忆..."
    python3 scripts/memory-system/enhanced_proactive_memory.py
fi

# 5. 创建启动快照
echo "📸 创建启动快照..."
python3 -c "
import sys
sys.path.insert(0, 'scripts/memory-system')
from session_persistence import SessionPersistence
sp = SessionPersistence()
sp.create_snapshot()
print('✅ 启动快照已创建')
"

echo "✅ 记忆系统启动恢复完成"
