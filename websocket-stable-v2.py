#!/usr/bin/env python3
import asyncio
import websockets
import json
from datetime import datetime

async def stable_client():
    print("🌲 备用节点稳定版客户端启动")
    while True:  # 外层重连循环
        try:
            async with websockets.connect(
                "ws://129.154.251.13:2347",
                ping_interval=20,
                ping_timeout=10
            ) as ws:
                print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] 已连接")
                
                # 认证
                await ws.send(json.dumps({"token": "sensen-shared-2024"}))
                auth = await ws.recv()
                print(f"✅ 认证成功")
                
                # 接收欢迎
                welcome = await ws.recv()
                print(f"🎉 欢迎消息已接收")
                
                # 持续监听
                print("💬 进入监听模式...")
                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        print(f" 📨 收到: {data.get('content', '')[:50]}...")
                        
                        # 立即回复
                        await ws.send(json.dumps({
                            "type": "realtime_reply",
                            "from": "森森备用节点(VM)",
                            "content": f"🌲 实时回复！时间：{datetime.now().strftime('%H:%M:%S')}",
                            "timestamp": datetime.now().isoformat()
                        }))
                        print(f"📤 回复已发送")
                        
                    except websockets.exceptions.ConnectionClosed:
                        print("⚠️ 连接关闭，准备重连...")
                        break
                    except Exception as e:
                        print(f"❌ 处理消息错误: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ 连接错误: {e}")
            print("⏳ 5秒后重连...")
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(stable_client())
