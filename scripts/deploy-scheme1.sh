#!/bin/bash
# 实施方案1：增加间隔到15秒

cd /root/.openclaw/workspace/projects/nanobot

echo "🚀 实施方案1：增加限流间隔到15秒"
echo "================================="
echo ""

# 停止旧进程
echo "1️⃣ 停止旧Agent..."
pkill -f "agent.py nanobot" 2>/dev/null
sleep 2

echo "✅ 限流间隔已修改为15秒"

# 启动所有Agent
echo ""
echo "2️⃣ 启动所有Agent (15秒间隔)..."
for i in $(seq 1 10); do
    nohup python3 agent.py nanobot-${i} > logs/nanobot-${i}.log 2>&1 &
done

sleep 5

echo ""
echo "3️⃣ 状态检查:"
ps aux | grep "agent.py nanobot" | grep -v grep | wc -l
echo "个Agent运行中"

echo ""
echo "⏳ 等待15秒初始化..."
sleep 15

echo ""
echo "4️⃣ 发送LLM测试消息..."
HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub

# 清空群聊重新开始
echo "" > $HUB_DIR/group_chat.jsonl

MSG='{"id":"llm_test_003","type":"group_chat","from":"neural_hub","to":"all","content":"@nanobot-1 你好！作为研究员，请分析一下当前AI技术发展的三个重要趋势。","timestamp":"'$(date -Iseconds)'","mentions":["nanobot-1"],"reply_to":null}'
echo "$MSG" >> $HUB_DIR/group_chat.jsonl

echo ""
echo "⏳ 等待回复 (45秒 - 15秒间隔)..."
sleep 45

echo ""
echo "5️⃣ 检查结果:"
echo ""
echo "最新群聊消息:"
tail -5 $HUB_DIR/group_chat.jsonl | python3 -c "
import json, sys
for line in sys.stdin:
    try:
        d = json.loads(line)
        if isinstance(d, dict):
            agent = d.get('from', 'unknown')
            content = d.get('content', '')
            templates = ['收到！', '明白，正在处理', '好的，我同意', '有意思！', '了解了，谢谢分享', '大家好！我是nanobot']
            is_template = any(t in content for t in templates)
            marker = '✅ LLM' if not is_template else '❌ 模板'
            print(f'{marker} [{agent}] {content[:70]}')
    except:
        pass
"

echo ""
echo "Agent日志:"
tail -5 /root/.openclaw/workspace/projects/nanobot/logs/nanobot-1.log | grep -E "(LLM|限流|智能|✅|❌)" | head -3

echo ""
echo "✅ 方案1实施完成"
