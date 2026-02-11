#!/bin/bash
# 记忆系统持续运行保障脚本
# 每小时执行一次，确保所有组件健康运行

LOG_FILE="/root/.openclaw/logs/memory-system-health.log"
ERR_FILE="/root/.openclaw/logs/memory-system-errors.log"

echo "[$(date)] 开始记忆系统健康检查..." >> "$LOG_FILE"

cd /root/.openclaw/workspace

# 1. 检查向量记忆系统
echo "[$(date)] 检查v5.2向量记忆..." >> "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, 'scripts/memory-system')
from vector_memory import get_vector_memory
vm = get_vector_memory()
no_vec = sum(1 for m in vm.memories.values() if not m.get('vector') and not m.get('embedding'))
if no_vec > 0:
    print(f'WARNING: {no_vec} memories without vectors')
    exit(1)
print(f'OK: {len(vm.memories)} memories with vectors')
" 2>>"$ERR_FILE" || echo "[$(date)] ❌ v5.2向量记忆异常" >> "$LOG_FILE"

# 2. 检查长期记忆
echo "[$(date)] 检查v5.1长期记忆..." >> "$LOG_FILE"
python3 -c "
import json
import os
if not os.path.exists('memory/long_term_memories.json'):
    print('ERROR: long_term_memories.json missing')
    exit(1)
with open('memory/long_term_memories.json') as f:
    lt = json.load(f)
if len(lt) < 10:
    print(f'WARNING: only {len(lt)} long-term memories')
print(f'OK: {len(lt)} long-term memories')
" 2>>"$ERR_FILE" || echo "[$(date)] ❌ v5.1长期记忆异常" >> "$LOG_FILE"

# 3. 检查快照系统
echo "[$(date)] 检查v5.5快照系统..." >> "$LOG_FILE"
SNAP_COUNT=$(ls memory/snapshots/snap_*.json 2>/dev/null | wc -l)
if [ "$SNAP_COUNT" -lt 1 ]; then
    echo "[$(date)] ❌ v5.5快照不足" >> "$LOG_FILE"
else
    echo "[$(date)] ✅ v5.5快照正常: $SNAP_COUNT个" >> "$LOG_FILE"
fi

# 4. 自动修复常见问题
echo "[$(date)] 执行自动修复..." >> "$LOG_FILE"

# 如果长期记忆为空，自动运行整理
if [ ! -f "memory/long_term_memories.json" ] || [ $(cat memory/long_term_memories.json 2>/dev/null | wc -l) -lt 10 ]; then
    echo "[$(date)] 自动运行v5.1记忆整理..." >> "$LOG_FILE"
    python3 scripts/memory-system/enhanced_layered_memory.py >> "$LOG_FILE" 2>&1
fi

# 5. 创建新快照
echo "[$(date)] 创建新快照..." >> "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, 'scripts/memory-system')
from session_persistence import SessionPersistence
sp = SessionPersistence()
sp.create_snapshot()
print('Snapshot created')
" >> "$LOG_FILE" 2>&1

echo "[$(date)] 健康检查完成" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
