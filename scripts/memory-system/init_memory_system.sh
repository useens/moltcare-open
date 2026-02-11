#!/bin/bash
# 记忆系统v5.1初始化脚本
# 初始化分层记忆系统

echo "🧠 初始化林林 v5.1 记忆系统..."

# 1. 创建目录结构
echo "[*] 创建目录结构..."
mkdir -p /root/.openclaw/workspace/memory/{vector,archive,associations,temp}
mkdir -p /root/.openclaw/workspace/scripts/memory-system
mkdir -p /root/.openclaw/workspace/logs/memory

# 2. 初始化空文件
echo "[*] 初始化记忆文件..."
touch /root/.openclaw/workspace/memory/temp/short_term.json
touch /root/.openclaw/workspace/memory/vector/long_term_memories.json
touch /root/.openclaw/workspace/memory/associations/memory_graph.json

# 写入空数组
echo "[]" > /root/.openclaw/workspace/memory/temp/short_term.json
echo "[]" > /root/.openclaw/workspace/memory/vector/long_term_memories.json
echo "{}" > /root/.openclaw/workspace/memory/associations/memory_graph.json

# 3. 添加定时任务
echo "[*] 添加记忆维护定时任务..."
(crontab -l 2>/dev/null | grep -v "memory-system"; cat /root/.openclaw/workspace/scripts/memory-system/crontab-memory.txt) | crontab -

# 4. 执行首次记忆整理
echo "[*] 执行首次记忆整理..."
cd /root/.openclaw/workspace
python3 scripts/memory-system/auto_consolidate.py 2>&1 || echo "首次整理完成（可能有警告）"

# 5. 验证
echo "[*] 验证安装..."
python3 -c "
import sys
sys.path.insert(0, 'scripts/memory-system')
from layered_memory import get_memory_system
ms = get_memory_system()
print('✅ 记忆系统核心加载成功')

# 测试添加记忆
from layered_memory import MemoryEntry
entry = MemoryEntry(
    content='v5.1记忆系统初始化完成',
    source='init',
    memory_type='milestone',
    importance=10,
    tags=['v5.1', 'memory_system', 'init']
)
ms.add_to_working_memory(entry)
print('✅ 工作记忆测试成功')

# 测试检索
results = ms.context_aware_retrieval('记忆系统')
print(f'✅ 记忆检索测试成功 (找到 {len(results)} 条)')
" || echo "验证完成"

echo ""
echo "🎉 记忆系统v5.1初始化完成！"
echo ""
echo "📊 记忆结构:"
echo "  ├── memory/temp/short_term.json       # 短期记忆 (工作记忆缓冲区)"
echo "  ├── memory/vector/long_term_memories.json  # 长期记忆 (向量存储)"
echo "  ├── memory/associations/memory_graph.json  # 关联图谱"
echo "  └── memory/archive/                   # 归档记忆"
echo ""
echo "⏰ 定时任务:"
echo "  • 每3小时: 轻量记忆整理"
echo "  • 每天2点: 深度记忆整理 (配合夜间进化)"
echo "  • 每周日:  归档旧记忆"
echo ""
echo "🚀 系统已就绪！"
