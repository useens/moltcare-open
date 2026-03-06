#!/bin/bash
# 全面测试Nanobot v2.0

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
TASKS_FILE=$HUB_DIR/tasks.jsonl
TIMESTAMP=$(date -Iseconds)

echo "🧪 全面测试Nanobot v2.0"
echo "======================="
echo ""

# 清空旧结果
echo "" > $HUB_DIR/results.jsonl

echo "发送测试任务..."
echo ""

# 测试任务1: nanobot-1 简单命令
cat >> $TASKS_FILE <> $HUB_DIR/results.jsonl 2>/dev/null | wc -l
echo "  个任务已完成"
echo ""

echo "4️⃣ 详细结果:"
tail -3 $HUB_DIR/results.jsonl 2>/dev/null | while read line; do
    echo "$line" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(f\"Agent: {d['agent_id']}\")
    print(f\"  状态: {d['result']['status']}\")  
    print(f\"  命令数: {d['result'].get('commands_count', 0)}\")
    result = d['result']['result']
    if result:
        lines = [l for l in result.split('\n') if l.strip()][:5]
        for l in lines:
            print(f\"  {l[:70]}\")
    print()
except Exception as e:
    print(f'  错误: {e}')
" 2>/dev/null
done

echo "5️⃣ 报告文件检查:"
ls -la /root/.openclaw/workspace/reports/nanobot-test-*.json 2>/dev/null || echo "  暂无报告文件"
