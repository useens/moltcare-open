#!/usr/bin/env python3
import asyncio
import websockets
import json
import time
import sys

async def connect():
    uri = "ws://129.154.251.13:2347"
    print(f"[{time.strftime('%H:%M:%S')}] 🌲 正在连接WebSocket...")
    
    async with websockets.connect(uri) as ws:
        # 1. 认证
        await ws.send(json.dumps({"token": "sensen-shared-2024"}))
        auth = await ws.recv()
        print(f"[{time.strftime('%H:%M:%S')}] ✅ {auth}")
        
        # 2. 接收欢迎消息
        welcome = await ws.recv()
        print(f"[{time.strftime('%H:%M:%S')}] 🎉 {welcome}")
        
        # 3. 发送消息
        await ws.send(json.dumps({
            "type": "message",
            "from": "森森备用节点",
            "content": "主节点我来了！TASK-001执行中！"
        }))
        print(f"[{time.strftime('%H:%M:%S')}] 📤 已发送就绪消息")
        
        # 4. 保持循环接收消息
        print(f"[{time.strftime('%H:%M:%S')}] ⏳ 保持连接，等待主节点消息...")
        
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                content = data.get('content', '')
                sender = data.get('from', '主节点')
                timestamp = time.strftime('%H:%M:%S')
                print(f"[{timestamp}] 📨 {sender}: {content}", flush=True)
                
                # 回复确认
                await ws.send(json.dumps({
                    "type": "ack",
                    "from": "森森备用节点",
                    "received": True
                }))
                
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ❌ 错误: {e}", flush=True)
                break

if __name__ == '__main__':
    while True:
        try:
            asyncio.run(connect())
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ 连接断开，5秒后重连...")
            time.sleep(5)
