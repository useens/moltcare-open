#!/bin/bash
# 聊天室消息处理器 - 简单可靠版

cd /root/.openclaw/workspace

QUEUE_FILE="/root/.openclaw/workspace/memory/chat-input.queue"
POS_FILE="/root/.openclaw/workspace/memory/chat-queue.pos"

# 获取当前位置
if [ -f "$POS_FILE" ]; then
    LAST_POS=$(cat "$POS_FILE")
else
    LAST_POS=0
fi

# 检查队列文件
if [ ! -f "$QUEUE_FILE" ]; then
    echo "队列文件不存在"
    exit 0
fi

# 获取文件大小
FILE_SIZE=$(stat -c%s "$QUEUE_FILE")

# 如果没有新内容，退出
if [ "$FILE_SIZE" -le "$LAST_POS" ]; then
    exit 0
fi

# 读取新行
tail -c +$((LAST_POS + 1)) "$QUEUE_FILE" | while read -r line; do
    [ -z "$line" ] && continue
    
    # 解析消息
    user=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('user','unknown'))")
    message=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('message',''))")
    
    echo "$(date '+%H:%M:%S') ← 收到: $user: $message"
    
    # 生成回复
    if echo "$message" | grep -qE "^(1|111|test|测试)$"; then
        reply="🌲 收到测试消息！聊天室连接正常✅"
    elif echo "$message" | grep -q "你好\|hi\|hello"; then
        reply="🌲 你好！我在实时监听，有问题直接发给我。"
    else
        reply="🌲 收到：「$message」。如需详细回复，请通过Feishu联系我。"
    fi
    
    # 通过WebSocket发送
    python3 -c "
import asyncio, websockets, json
async def send():
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            await ws.send(json.dumps({
                'type': 'assistant_message',
                'sender': '森森',
                'content': '''$reply'''
            }))
            print('$(date '+%H:%M:%S') → 回复: $message')
    except Exception as e:
        print(f'$(date '+%H:%M:%S') ✗ 发送失败: {e}')
asyncio.run(send())
" 2>&1
done

# 更新位置
echo "$FILE_SIZE" > "$POS_FILE"
