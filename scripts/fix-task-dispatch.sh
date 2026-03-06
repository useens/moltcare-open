#!/bin/bash
# 修正任务分发机制 - 写入正确的 tasks.jsonl
# Agent只读取 hub/tasks.jsonl，不读取 inbox/*.json

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
TASKS_FILE=$HUB_DIR/tasks.jsonl

echo "🔄 修正任务分发机制"
echo "==================="
echo ""

# 清空错误的inbox任务
echo "清理错误的inbox任务..."
rm -f $HUB_DIR/inbox/*_script_audit.json
echo "✅ 已清理 inbox/*_script_audit.json"
echo ""

# 按正确格式写入tasks.jsonl
echo "写入正确的任务格式到 tasks.jsonl..."

# nanobot-1 研究员: Moltbook脚本分析
cat >> $TASKS_FILE <> $TASKS_FILE <> $TASKS_FILE <> $TASKS_FILE << 'EOF'
{"type":"task","agent_id":"nanobot-8","data":{"description":"分析316个Python脚本的活跃状态。\n\n任务:\n1. 检查哪些脚本30天内未被访问\n2. 检查哪些脚本在cron中被引用\n3. 检查哪些脚本有运行中的进程\n4. 生成活跃/废弃脚本清单\n\n输出格式:\n- 活跃脚本列表\n- 废弃脚本列表(可删除候选)","priority":"high","context":"ops"},"timestamp":"$(date -Iseconds)"}
EOF

echo "✅ 已写入4个审计任务到 tasks.jsonl"
echo ""

# 显示任务队列尾部
echo "任务队列最新内容:"
tail -4 $TASKS_FILE
echo ""

# 检查Agent日志
echo "Agent状态检查:"
for i in 1 4 7 8; do
    pid_file="$HUB_DIR/../logs/nanobot-${i}.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "  nanobot-${i}: ✅ 运行中 (PID $pid)"
        else
            echo "  nanobot-${i}: ❌ 未运行"
        fi
    fi
done
echo ""
echo "📊 任务已分发，等待Agent处理..."
echo "监控日志: tail -f $HUB_DIR/../logs/nanobot-1.log"
