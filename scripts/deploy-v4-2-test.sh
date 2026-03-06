#!/bin/bash
# 部署v4.2限流版并测试LLM

cd /root/.openclaw/workspace/projects/nanobot

echo "🚀 部署v4.2限流版"
echo "=================="

# 部署
cp agent_v4_2_rate_limit.py agent.py
echo "✅ v4.2已部署"

# 停止旧进程
echo ""
echo "停止旧Agent..."
pkill -f "agent.py nanobot" 2>/dev/null
sleep 2

# 启动所有Agent
echo ""
echo "启动所有Agent (限流版)..."
for i in $(seq 1 10); do
    nohup python3 agent.py nanobot-${i} > logs/nanobot-${i}.log 2>&1 &
done

sleep 5

echo ""
echo "状态检查:"
ps aux | grep "agent.py nanobot" | grep -v grep | wc -l
echo "个Agent运行中"

echo ""
echo "⏳ 等待10秒初始化..."
sleep 10

echo ""
echo "发送LLM测试消息..."
HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub

MSG='{"id":"llm_test_002","type":"group_chat","from":"neural_hub","to":"all","content":"@nanobot-1 你好！请分享一个关于AI发展的有趣观点。","timestamp":"'$(date -Iseconds)'","mentions":["nanobot-1"],"reply_to":null}'
echo "$MSG" >> $HUB_DIR/group_chat.jsonl

echo ""
echo "等待回复 (30秒)..."
sleep 30

echo ""
echo "📊 检查结果:"
tail -5 $HUB_DIR/group_chat.jsonl | python3 -c "
import json, sys
for line in sys.stdin:
    try:
        d = json.loads(line)
        if isinstance(d, dict) and d.get('from') == 'nanobot-1':
            content = d.get('content', '')
            # 判断是否是模板
            templates = ['收到！', '明白，正在处理', '好的，我同意', '有意思！', '了解了，谢谢分享']
            is_template = any(t in content for t in templates)
            if is_template:
                print(f'❌ 模板回复: {content}')
            else:
                print(f'✅ 智能回复: {content[:80]}...')
    except:
        pass
"

echo ""
echo "✅ 部署完成"
