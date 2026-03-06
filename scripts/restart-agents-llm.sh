#!/bin/bash
# 重启所有Agent以启用LLM模式

cd /root/.openclaw/workspace/projects/nanobot

echo "🔄 重启Agent启用LLM模式"
echo "========================="

# 停止旧进程
echo "1️⃣ 停止旧Agent..."
pkill -f "agent.py nanobot" 2>/dev/null
sleep 2

# 清空群聊，重新开始
echo ""
echo "2️⃣ 备份并重置群聊记录..."
cp hub/group_chat.jsonl hub/group_chat.jsonl.backup.$(date +%H%M%S)
echo "" > hub/group_chat.jsonl

# 启动所有Agent
echo ""
echo "3️⃣ 启动所有Agent (LLM模式)..."
for i in $(seq 1 10); do
    nohup python3 agent.py nanobot-${i} > logs/nanobot-${i}.log 2>&1 &
echo "  nanobot-${i} 已启动 (LLM模式)"
    sleep 0.5
done

sleep 5

echo ""
echo "4️⃣ 状态检查:"
ps aux | grep "agent.py nanobot" | grep -v grep | wc -l
echo "  个Agent运行中"

echo ""
echo "✅ 所有Agent已切换到LLM模式"
echo "💡 新发送的消息将使用LLM生成智能回复"
echo ""
echo "⏳ 等待10秒让Agent初始化..."
sleep 10

echo ""
echo "📊 最新群聊消息:"
tail -5 hub/group_chat.jsonl | python3 -c "
import json, sys
for line in sys.stdin:
    try:
        d = json.loads(line)
        if isinstance(d, dict):
            print(f\"  [{d.get('from', 'unknown')}] {d.get('content', '')[:60]}\")
    except:
        pass
" 2>/dev/null || echo "  暂无新消息"
