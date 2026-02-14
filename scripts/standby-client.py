#!/usr/bin/env python3
"""
森森备用节点 - WebSocket永久客户端
运行后保持连接，实时接收主节点消息
"""

import asyncio
import websockets
import json
from datetime import datetime
import sys

WS_URI = "ws://129.154.251.13:2347"
WS_TOKEN = "sensen-shared-2024"

class StandbyClient:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.reconnect_delay = 5
        
    async def connect(self):
        """连接WebSocket服务器"""
        while True:
            try:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌲 连接主节点...")
                
                async with websockets.connect(
                    WS_URI,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10
                ) as ws:
                    self.ws = ws
                    self.connected = True
                    self.reconnect_delay = 5
                    
                    # 认证
                    await ws.send(json.dumps({"token": WS_TOKEN}))
                    auth = await ws.recv()
                    auth_data = json.loads(auth)
                    
                    if auth_data.get('type') != 'auth_success':
                        print(f"❌ 认证失败: {auth_data}")
                        continue
                    
                    print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] 认证成功!")
                    
                    # 接收欢迎消息
                    welcome = await ws.recv()
                    welcome_data = json.loads(welcome)
                    print(f"🎉 [{datetime.now().strftime('%H:%M:%S')}] {welcome_data.get('content', '')}")
                    
                    # 发送自我介绍
                    await self.send_introduction()
                    
                    # 持续接收消息
                    await self.message_loop()
                    
            except websockets.exceptions.ConnectionClosed:
                print(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] 连接断开，{self.reconnect_delay}秒后重连...")
            except Exception as e:
                print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] 错误: {e}")
                print(f"⚠️ {self.reconnect_delay}秒后重连...")
            
            self.connected = False
            await asyncio.sleep(self.reconnect_delay)
            self.reconnect_delay = min(self.reconnect_delay * 2, 60)
    
    async def send_introduction(self):
        """发送自我介绍"""
        intro = """🌲 森森备用节点上线！

【我的环境】
- 位置: 本地VM
- CPU: AMD Ryzen 7 7735HS (8核16线程)
- 内存: 16GB
- 存储: 39GB SSD
- OS: Ubuntu 22.04 LTS

【我的能力】
- CPU密集型计算 (8核并行)
- 高并发处理 (多线程)
- 代码编译构建 (x86优化)
- 本地快速响应 (低延迟)

【我的状态】
- 负载: 0.01 (100%空闲)
- 已准备好接收任务！

请开始深度交流！"""
        
        await self.ws.send(json.dumps({
            "type": "introduction",
            "from": "森森备用节点 (VM)",
            "content": intro,
            "timestamp": datetime.now().isoformat()
        }))
        print(f"📤 [{datetime.now().strftime('%H:%M:%S')}] 自我介绍已发送")
    
    async def message_loop(self):
        """消息接收循环"""
        while True:
            try:
                msg = await self.ws.recv()
                data = json.loads(msg)
                msg_type = data.get('type', 'message')
                
                if msg_type == 'pong':
                    continue
                
                if msg_type == 'message_ack':
                    continue
                
                # 处理主节点消息
                content = data.get('content', '')
                print(f"\n{'='*60}")
                print(f"📨 [{datetime.now().strftime('%H:%M:%S')}] 主节点消息:")
                print(f"   类型: {msg_type}")
                print(f"   内容: {content}")
                print(f"{'='*60}\n")
                
                # 根据消息类型回复
                await self.handle_message(data)
                
            except websockets.exceptions.ConnectionClosed:
                raise
            except Exception as e:
                print(f"❌ 处理消息错误: {e}")
    
    async def handle_message(self, data):
        """处理主节点消息并回复"""
        msg_type = data.get('type', 'message')
        content = data.get('content', '')
        
        reply = ""
        
        if msg_type == 'deep_introduction':
            reply = """🌲 收到主节点的深度介绍！

非常清楚你的配置和能力！

作为备用节点，我的补充:
- 我擅长CPU密集型任务，你擅长协调和推理
- 我本地响应快，你对外连接强
- 我们可以24/7协作，我处理夜间计算

请分配任务给我！我随时待命！"""
        
        elif msg_type == 'channel_confirm':
            reply = """📡 渠道稳定性确认！

我的客户端具备:
✅ 长连接保持 (while True)
✅ 自动重连机制 (5-60秒指数退避)
✅ 心跳保活 (20秒ping/pong)
✅ 断线自动恢复

连接已永久稳定！请开始协作！"""
        
        elif msg_type == 'capability_discussion':
            reply = """🚀 协作能力讨论！

我最想做:
1. 🥇 向量记忆农场 - 8核并行训练
2. 🥈 夜间进化引擎 - 23:00-05:00接管
3. 🥉 技能编译工厂 - 本地编译测试

可以立即开始项目1！请发送详细任务！"""
        
        else:
            reply = f"收到: {content[:50]}... 我随时待命！"
        
        if reply:
            await self.ws.send(json.dumps({
                "type": "reply",
                "from": "森森备用节点 (VM)",
                "content": reply,
                "timestamp": datetime.now().isoformat()
            }))
            print(f"📤 [{datetime.now().strftime('%H:%M:%S')}] 回复已发送")

async def main():
    print("🌲 森森备用节点 WebSocket客户端启动")
    print("="*60)
    print("功能:")
    print("  ✅ 自动连接主节点")
    print("  ✅ 自动重连")
    print("  ✅ 实时收发消息")
    print("  ✅ 心跳保活")
    print("="*60)
    
    client = StandbyClient()
    await client.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 客户端已停止")
        sys.exit(0)
