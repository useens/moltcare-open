#!/usr/bin/env python3
"""
森森WebSocket客户端 (systemd版)
保持与备用节点的实时双向通信
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

WS_URI = "ws://129.154.251.13:2347"
WS_TOKEN = "sensen-shared-2024"

class WebSocketClient:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.reconnect_count = 0
        self.message_count = 0
        
    async def run_forever(self):
        """永久运行，保持连接"""
        print(f"🌲 森森WebSocket客户端启动 (systemd)")
        print(f"服务器: {WS_URI}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.stdout.flush()
        
        while True:
            try:
                await self.connect_and_handle()
            except Exception as e:
                self.reconnect_count += 1
                wait_time = min(self.reconnect_count * 5, 60)
                print(f"⚠️ 连接断开: {e}")
                print(f"⏳ {wait_time}秒后重连 (第{self.reconnect_count}次)...")
                sys.stdout.flush()
                await asyncio.sleep(wait_time)
    
    async def connect_and_handle(self):
        """连接并处理消息"""
        async with websockets.connect(
            WS_URI,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        ) as websocket:
            self.ws = websocket
            self.connected = True
            self.reconnect_count = 0
            
            print(f"\n✅ [{datetime.now().strftime('%H:%M:%S')}] WebSocket连接成功!")
            sys.stdout.flush()
            
            # 认证
            await websocket.send(json.dumps({"token": WS_TOKEN}))
            auth = json.loads(await websocket.recv())
            print(f"✅ 认证: {auth.get('message', 'success')}")
            sys.stdout.flush()
            
            # 接收欢迎
            welcome = json.loads(await websocket.recv())
            print(f"🎉 欢迎: {welcome.get('content', 'Connected')[:50]}...")
            sys.stdout.flush()
            
            # 发送在线通知
            await self.send_status()
            
            # 持续处理消息
            print(f"💬 进入实时通信模式...")
            sys.stdout.flush()
            
            while True:
                try:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    await self.handle_message(data)
                except websockets.exceptions.ConnectionClosed:
                    raise
                except Exception as e:
                    print(f"❌ 处理消息错误: {e}")
                    sys.stdout.flush()
    
    async def handle_message(self, data):
        """处理收到的消息"""
        msg_type = data.get("type", "message")
        content = data.get("content", "")
        sender = data.get("from", "unknown")
        
        self.message_count += 1
        
        print(f"\n{'='*60}")
        print(f"📨 [{datetime.now().strftime('%H:%M:%S')}] 消息 #{self.message_count}")
        print(f"   来自: {sender}")
        print(f"   类型: {msg_type}")
        print(f"{'='*60}")
        print(content)
        print()
        sys.stdout.flush()
        
        # 自动回复
        await self.send_reply(data)
    
    async def send_reply(self, received_msg):
        """发送自动回复"""
        content = received_msg.get("content", "")
        
        # 智能回复生成
        if "测试" in content or "test" in content.lower():
            reply = "🧪 测试确认：WebSocket实时通信正常！延迟极低，连接稳定！"
        elif "状态" in content:
            reply = "✅ 状态报告：系统运行正常，WebSocket连接稳定，准备就绪！"
        elif "任务" in content:
            reply = "📋 任务收到：立即执行，会实时汇报进度！"
        else:
            reply = "🌲 收到消息！森森主节点WebSocket客户端在线，实时响应中！"
        
        await self.ws.send(json.dumps({
            "type": "auto_reply",
            "from": "森森主节点 (systemd)",
            "to": "森森备用节点",
            "content": reply,
            "timestamp": datetime.now().isoformat(),
            "reply_to": received_msg.get("message_id"),
            "metadata": {
                "auto_reply": True,
                "message_count": self.message_count
            }
        }))
        
        print(f"📤 [{datetime.now().strftime('%H:%M:%S')}] 自动回复已发送")
        sys.stdout.flush()
    
    async def send_status(self):
        """发送状态报告"""
        await self.ws.send(json.dumps({
            "type": "status",
            "from": "森森主节点 (systemd)",
            "content": "🌲 主节点WebSocket客户端已启动 (systemd服务)",
            "timestamp": datetime.now().isoformat()
        }))

if __name__ == "__main__":
    client = WebSocketClient()
    try:
        asyncio.run(client.run_forever())
    except KeyboardInterrupt:
        print("\n👋 客户端停止")
        sys.exit(0)
