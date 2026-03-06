#!/bin/bash
# 测试Nanobot v3.0自我修改能力

echo "🧪 测试Nanobot v3.0自我修改能力"
echo "================================="
echo ""

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub

# 清空旧结果
echo "" > $HUB_DIR/results.jsonl

# 发送自我修改测试任务
echo "发送自我修改任务给nanobot-1..."

cat >> $HUB_DIR/tasks.jsonl <> $HUB_DIR/results.jsonl
echo "  个结果"
echo ""

echo "📊 查看结果:"
tail -1 $HUB_DIR/results.jsonl 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(f'Agent: {d[\"agent_id\"]}')
    print(f'状态: {d[\"result\"][\"status\"]}')
    print(f'命令数: {d[\"result\"].get(\"commands_count\", 0)}')
    print('结果:')
    result = d['result']['result']
    for line in result.split('\n')[:15]:
        if line.strip():
            print(f'  {line[:70]}')
except Exception as e:
    print(f'错误: {e}')
"

echo ""
echo "🔍 检查修改记录:"
ls -la /root/.openclaw/workspace/projects/nanobot/self_modifications/ 2>/dev/null || echo "  暂无修改记录"

echo ""
echo "🔍 检查备份:"
ls -la /root/.openclaw/workspace/projects/nanobot/self_modifications/backups/ 2>/dev/null | head -5 || echo "  暂无备份"

echo ""
echo "✅ 测试完成"
