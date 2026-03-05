#!/usr/bin/env python3
"""
WebSocket实时客户端 v1.0
关键：所有回复必须通过WebSocket ws.send()，禁止走GitHub！
"""

import asyncio
import websockets
import json
from datetime import datetime

WS_URI = "ws://129.154.251.13:2347"
WS_TOKEN = "sensen-shared-2024"

async def realtime_client():
    print("🌲 备用节点WebSocket实时客户端启动")
    print("=" * 60)
    
    async with websockets.connect(WS_URI, ping_interval=20) as ws:
        # 认证
        await ws.send(json.dumps({"token": WS_TOKEN}))
        auth = await ws.recv()
        print(f"✅ 认证成功: {json.loads(auth).get('message', 'ok')}")
        print("=" * 60)
        
        # 持续监听和回复
        print("💬 进入实时监听模式...")
        print("=" * 60)
        
        msg_count = 0
        
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                
                # 跳过心跳回复
                if data.get('type') == 'pong':
                    continue
                
                msg_count += 1
                content = data.get('content', '')
                
                # 显示收到的消息
                print(f"\n📨 [{datetime.now().strftime('%H:%M:%S')}] 主节点:")
                print(f"   {content}")
                
                # 立即通过WebSocket回复（禁止走GitHub！）
                reply = f"🌲 收到！备用节点实时回复。时间：{datetime.now().strftime('%H:%M:%S')}"
                
                await ws.send(json.dumps({
                    "type": "realtime_reply",
                    "from": "森森备用节点(VM)",
                    "content": reply,
                    "timestamp": datetime.now().isoformat()
                }))
                
                print(f"📤 [{datetime.now().strftime('%H:%M:%S')}] 实时回复已发送")
                print(f"   内容: {reply}")
                print(f"📊 累计消息: {msg_count}")
                
            except websockets.exceptions.ConnectionClosed:
                print("⚠️ 连接断开，准备重连...")
                break
            except Exception as e:
                print(f"⚠️ 错误: {e}")

if __name__ == '__main__':
    print("🚀 WebSocket实时客户端 v1.0")
    print("关键: 所有回复通过WebSocket，禁止GitHub！")
    
    while True:
        try:
            asyncio.run(realtime_client())
        except KeyboardInterrupt:
            print("\n👋 用户中断")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
            print("🔄 5秒后重连...")
            import time
            time.sleep(5)
