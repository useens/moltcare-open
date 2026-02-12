#!/bin/bash
# 超进化模式深度学习循环
# Hyper-Evolution Deep Learning Loop
# 每30分钟执行一次高强度深度学习

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
STATE_FILE="$WORKSPACE_DIR/memory/hyper-evolution-state.json"
LOG_FILE="$WORKSPACE_DIR/memory/logs/hyper-evolution.log"

cd "$WORKSPACE_DIR"

# 检查是否在超进化模式
if [ ! -f "$STATE_FILE" ]; then
    echo "状态文件不存在，退出" >> "$LOG_FILE"
    exit 0
fi

IS_ACTIVE=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('active', False))")
if [ "$IS_ACTIVE" != "True" ]; then
    echo "超进化模式未激活，跳过本次循环" >> "$LOG_FILE"
    exit 0
fi

echo "$(date): 开始超进化深度学习循环" >> "$LOG_FILE"

# ============ 1. 高强度情报收集 ============
echo "=== 阶段1: 高强度情报收集 ===" >> "$LOG_FILE"

# 运行深度学习脚本 (Signal阈值=6，比正常的7更积极)
python3 scripts/collect-web-intel-hyper.py >> "$LOG_FILE" 2>&1 || true

# ============ 2. 学习债务处理 ============
echo "=== 阶段2: 学习债务处理 ===" >> "$LOG_FILE"

if [ -f "memory/learning-debt.md" ]; then
    # 处理学习债务
    python3 scripts/process-learning-debt.py --limit 5 >> "$LOG_FILE" 2>&1 || true
fi

# ============ 3. 知识内化 ============
echo "=== 阶段3: 知识内化 ===" >> "$LOG_FILE"

# 运行知识内化流程
python3 scripts/internalize-knowledge.py >> "$LOG_FILE" 2>&1 || true

# ============ 4. 应用检验 ============
echo "=== 阶段4: 应用检验 ===" >> "$LOG_FILE"

# 检验最近的改进效果
python3 scripts/validate-improvements.py >> "$LOG_FILE" 2>&1 || true

# ============ 5. 更新状态统计 ============
python3 -c "
import json
from datetime import datetime

with open('$STATE_FILE', 'r') as f:
    state = json.load(f)

state['deep_learning_count'] = state.get('deep_learning_count', 0) + 1
state['last_run'] = datetime.now().isoformat()

with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
" >> "$LOG_FILE" 2>&1

echo "$(date): 超进化深度学习循环完成" >> "$LOG_FILE"

# ============ 6. 检查结束条件 ============
python3 -c "
import json
import sys
from datetime import datetime

with open('$STATE_FILE', 'r') as f:
    state = json.load(f)

# 检查时间条件
if state.get('scheduled_end'):
    end_time = datetime.fromisoformat(state['scheduled_end'])
    if datetime.now() >= end_time:
        print('DURATION_REACHED')
        sys.exit(0)

# 检查里程碑条件 (简单示例)
if state.get('milestone') == 'version-release':
    # 这里可以检查是否有新版本发布
    pass

print('CONTINUE')
" | grep -q "DURATION_REACHED" && {
    echo "$(date): 达到持续时间，准备停止超进化模式" >> "$LOG_FILE"
    python3 scripts/hyper-evolution.py stop --reason "duration_reached"
}
