#!/bin/bash
# Whisper Server v2.0 功能演示

echo "================================"
echo "Whisper Server v2.0 功能演示"
echo "================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT="$SCRIPT_DIR/client_v2.py"
VENV_PYTHON="$SCRIPT_DIR/../.venv/bin/python"

# 测试音频
AUDIO="/root/.openclaw/media/inbound/82f421eb-fa43-4d72-9da9-e09cf9e0a0c9.ogg"

echo "1. 同步转录 (直接返回结果)"
echo "   $ whisper-daemon-v2 audio.ogg"
echo "   结果:"
time $VENV_PYTHON "$CLIENT" "$AUDIO" -l zh 2>/dev/null
echo ""

echo "2. 异步转录 (返回任务ID)"
echo "   $ whisper-daemon-v2 audio.ogg --async"
TASK_RESULT=$($VENV_PYTHON "$CLIENT" "$AUDIO" -l zh --async 2>&1)
echo "   $TASK_RESULT"
TASK_ID=$(echo "$TASK_RESULT" | grep "Task queued" | awk '{print $3}')
echo ""

echo "3. 查询异步结果"
echo "   $ whisper-daemon-v2 --query $TASK_ID"
$VENV_PYTHON "$CLIENT" --query "$TASK_ID" 2>&1
echo ""

echo "4. 服务器统计"
echo "   $ whisper-daemon-v2 --stats"
$VENV_PYTHON "$CLIENT" --stats 2>&1
echo ""

echo "================================"
echo "所有功能测试完成!"
echo "================================"
