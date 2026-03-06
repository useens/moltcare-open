#!/bin/bash
# 使用Nanobot v2.0执行完整审计

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
TASKS_FILE=$HUB_DIR/tasks.jsonl
TIMESTAMP=$(date -Iseconds)

echo "🤖 使用Nanobot v2.0执行完整审计"
echo "==============================="
echo ""

# 清空旧结果
echo "" > $HUB_DIR/results.jsonl

# 任务1: nanobot-1 研究员 - 脚本清单
cat >> $TASKS_FILE <> $HUB_DIR/results.jsonl 2>/dev/null | while read line; do
    echo "$line" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    agent = d['agent_id']
    status = d['result']['status']
    cmds = d['result'].get('commands_count', 0)
    result = d['result']['result']
    print(f\"✅ {agent}: {status} ({cmds}个命令)\")
    if result and len(result) > 50:
        preview = result.replace('\n', ' ')[:100]
        print(f\"   结果: {preview}...\")
except:
    pass
" 2>/dev/null
done

echo ""
echo "📁 检查生成的报告:"
ls -la /root/.openclaw/workspace/reports/nanobot-v2-*.json 2>/dev/null || echo "  正在生成..."
