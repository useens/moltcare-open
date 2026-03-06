#!/bin/bash
# 发送测试任务验证Nanobot v2.0

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
TASKS_FILE=$HUB_DIR/tasks.jsonl
TIMESTAMP=$(date -Iseconds)

echo "🧪 发送测试任务验证Nanobot v2.0"
echo "================================"
echo ""

# 清空旧结果
echo "" > $HUB_DIR/results.jsonl

# 测试任务1: 简单命令执行
cat >> $TASKS_FILE <> $HUB_DIR/results.jsonl 2>/dev/null | while read line; do
    echo "$line" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(f\"Agent: {d['agent_id']}\")
    print(f\"  状态: {d['result']['status']}\")
    print(f\"  执行命令数: {d['result'].get('commands_count', 0)}\")
    result = d['result']['result']
    if result:
        lines = result.split('\n')[:10]
        for l in lines:
            if l.strip():
                print(f\"  {l[:100]}\")
    print()
except Exception as e:
    print(f'  解析错误: {e}')
" 2>/dev/null
done

echo ""
echo "检查报告文件:"
ls -la /root/.openclaw/workspace/reports/nanobot-*-test.json 2>/dev/null || echo "  暂无报告文件"
