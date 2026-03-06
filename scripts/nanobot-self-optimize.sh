#!/bin/bash
# 让十个小弟自己优化自己

echo "🤖 通知十个小弟：自己优化自己"
echo "==============================="
echo ""

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
TIMESTAMP=$(date -Iseconds)

echo "" > $HUB_DIR/results.jsonl

# 创建自我优化任务
cat > /tmp/self_optimize_tasks.txt <> $HUB_DIR/tasks.jsonl
    echo "✅ 已通知 $agent ($role)"
done

echo ""
echo "⏳ 等待小弟们自我优化 (30秒)..."
sleep 30

echo ""
echo "📊 检查结果:"
echo "完成的任务数: $(wc -l < $HUB_DIR/results.jsonl)"
echo ""

echo "各小弟优化状态:"
for i in $(seq 1 10); do
    agent="nanobot-$i"
    log_file="/root/.openclaw/workspace/projects/nanobot/logs/${agent}.log"
    if [ -f "$log_file" ]; then
        last_action=$(tail -3 "$log_file" 2>/dev/null | grep -E "(完成|优化|修改)" | tail -1)
        if [ -n "$last_action" ]; then
            echo "  $agent: $last_action"
        fi
    fi
done

echo ""
echo "✅ 自我优化任务分发完成"
