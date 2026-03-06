#!/bin/bash
# 停止神经中枢 2.0

cd /root/.openclaw/workspace

echo "🛑 停止神经中枢 2.0..."

# 停止nanobot
echo "  停止 Nanobot V3..."
./ai-nanobots/stop-all-v3.sh 2>/dev/null || true

# 停止神经中枢
if [ -f "data/neural_hub/hub.pid" ]; then
    pid=$(cat data/neural_hub/hub.pid)
    if kill -0 "$pid" 2>/dev/null; then
        echo "  停止 神经中枢 (PID: $pid)..."
        kill "$pid"
    fi
    rm -f data/neural_hub/hub.pid
fi

echo ""
echo "✅ 神经中枢 2.0 已停止"
