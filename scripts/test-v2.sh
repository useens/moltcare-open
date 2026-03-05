#!/bin/bash
# 彻底重启V2

echo "停止所有nanobot..."
pkill -9 -f "nanobot_v2\|simple_nanobot\|nanobot.py" 2>/dev/null
sleep 3

echo "启动nanobot-1 V2测试..."
cd /root/.openclaw/workspace/ai-nanobots
python3 nanobot_v2.py nanobot-1 > nanobot-1.log 2>&1 &
sleep 3

echo "检查："
ps aux | grep "nanobot_v2" | grep -v grep

echo ""
echo "测试通信："
curl -s http://localhost:19000/poll/openclaw > /dev/null
curl -s -X POST http://localhost:19000/message \
  -H "Content-Type: application/json" \
  -d '{"from":"openclaw","to":"nanobot-1","message":"status"}'
echo ""
sleep 5
echo "收到回复："
curl -s http://localhost:19000/poll/openclaw
