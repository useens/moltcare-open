#!/bin/bash
# 启动10个AI nanobot

echo "======================================================================"
echo "🚀 启动10个AI nanobot"
echo "======================================================================"
echo ""

BASE_DIR="/root/.openclaw/workspace/ai-nanobots"

# 停止旧的nanobot进程
echo "1. 停止旧的nanobot进程..."
pkill -f "ai-nanobots/nanobot-.*.py" 2>/dev/null
pkill -f "workspace/nanobot/nanobot.py" 2>/dev/null
sleep 2
echo "   ✅ 旧进程已停止"
echo ""

# 启动10个新的AI nanobot
echo "2. 启动10个AI nanobot..."
for i in {1..10}; do
    NB_ID="nanobot-${i}"
    NB_DIR="${BASE_DIR}/${NB_ID}"

    if [ -d "$NB_DIR" ]; then
        cd "$NB_DIR"
        nohup python3 nanobot.py > ${NB_DIR}/start.log 2>&1 &
        PID=$!
        echo "   ✅ ${NB_ID} 启动 (PID: ${PID})"
    else
        echo "   ❌ ${NB_DIR} 不存在"
    fi
done

echo ""
echo "3. 等待启动..."
sleep 5

echo ""
echo "4. 检查状态:"
ps aux | grep "ai-nanobots" | grep -v grep | head -10

echo ""
echo "======================================================================"
echo "✅ 10个AI nanobot已启动！"
echo "======================================================================"
 echo ""
echo "查看日志:"
echo "  tail -f ai-nanobots/nanobot-1/nanobot-1.log"
echo ""
echo "测试通信:"
echo "  curl -X POST http://localhost:19000/message \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"from\":\"openclaw\",\"to\":\"nanobot-1\",\"message\":\"你好\"}'"
echo "======================================================================"
