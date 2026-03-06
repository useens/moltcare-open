#!/bin/bash
# 重启所有Agent到v4.1修复版

cd /root/.openclaw/workspace/projects/nanobot

# 停止旧进程
pkill -f "agent.py nanobot" 2>/dev/null
sleep 2

# 修复group_chat.jsonl格式 - 移除开头的[]
if head -1 hub/group_chat.jsonl | grep -q '^\[\]'; then
    tail -n +2 hub/group_chat.jsonl > hub/group_chat.jsonl.tmp
    mv hub/group_chat.jsonl.tmp hub/group_chat.jsonl
fi

# 启动10个Agent
for i in 1 2 3 4 5 6 7 8 9 10; do
    nohup python3 agent.py nanobot-${i} > logs/nanobot-${i}.log 2>&1 &
done

sleep 5

# 检查状态
echo "Agent状态:"
ps aux | grep "agent.py nanobot" | grep -v grep | wc -l
echo "个运行中"

# 等待互动
echo "等待互动..."
sleep 10

# 查看新消息
echo ""
echo "最新群聊消息:"
tail -5 hub/group_chat.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        if isinstance(d, dict):
            print(f\"  [{d.get('from', 'unknown')}] {d.get('content', '')[:60]}\")
    except:
        pass
"
