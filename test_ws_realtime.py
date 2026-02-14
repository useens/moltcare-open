#!/usr/bin/env python3
import asyncio
import websockets
import json

async def connect():
    async with websockets.connect("ws://129.154.251.13:2347") as ws:
        # 认证
        await ws.send(json.dumps({"token": "sensen-shared-2024"}))
        auth = await ws.recv()
        print(f"认证: {auth}")
        
        # 接收欢迎消息
        welcome = await ws.recv()
        print(f"欢迎: {welcome}")
        
        # 持续监听
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"收到: {data}")
            
            # 回复
            await ws.send(json.dumps({
                "type": "reply",
                "content": "🌲 备用节点实时回复！"
            }))
            print("📤 回复已发送")

asyncio.run(connect())
