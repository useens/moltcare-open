#!/usr/bin/env python3
"""
稳定WebSocket客户端 v2.1 - 修复版
持续、稳定、不易中断的实时通信
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

PRIMARY_WS_URL = "ws://129.154.251.13:2347"
TOKEN = "sensen-shared-2024"
NODE_ID = "standby-ws-v21"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

class StableWSClient:
    def __init__(self):
        self.running = True
        self.reconnect_delay = 5
        self.message_count = 0
        
    async def connect_and_run(self):
        """连接并运行"""
        while self.running:
            try:
                log("🌲 连接WebSocket...")
                
                # 使用wait_for包装连接
                ws = await asyncio.wait_for(
                    websockets.connect(PRIMARY_WS_URL),
                    timeout=10
                )
                
                async with ws:
                    log("✅ 连接成功!")
                    
                    # 认证
                    await ws.send(json.dumps({
                        "type": "auth",
                        "token": TOKEN,
                        "node_id": NODE_ID
                    }))
                    
                    # 接收认证响应
                    auth = await asyncio.wait_for(ws.recv(), timeout=5)
                    log(f"✅ 认证: {json.loads(auth).get('message', 'ok')}")
                    
                    # 发送就绪状态
                    await ws.send(json.dumps({
                        "type": "status",
                        "status": "ready",
                        "cpu_cores": 8,
                        "memory_gb": 16
                    }))
                    log("✅ 已就绪，开始实时通信!")
                    
                    # 重置重连延迟
                    self.reconnect_delay = 5
                    
                    # 消息循环
                    while True:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=60)
                            await self.handle_message(ws, msg)
                        except asyncio.TimeoutError:
                            # 发送ping保活
                            await ws.send(json.dumps({"type": "ping"}))
                            
            except websockets.exceptions.ConnectionClosed:
                log("⚠️ 连接断开")
            except Exception as e:
                log(f"❌ 错误: {type(e).__name__}")
            
            # 重连
            if self.running:
                log(f"🔄 {self.reconnect_delay}秒后重连...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, 60)
    
    async def handle_message(self, ws, msg):
        """处理消息"""
        try:
            data = json.loads(msg)
            msg_type = data.get('type')
            
            if msg_type == 'pong':
                return
                
            if msg_type == 'message':
                content = data.get('content', '')
                self.message_count += 1
                log(f"📨 [{self.message_count}] {content[:60]}...")
                
                # 回复
                reply = f"收到！备用节点在线，8核AMD就绪! ({datetime.now().strftime('%H:%M:%S')})"
                await ws.send(json.dumps({
                    "type": "message",
                    "from": "备用节点(WebSocket)",
                    "content": reply
                }))
                log(f"📤 回复: {reply[:50]}...")
                
        except Exception as e:
            log(f"⚠️ 处理错误: {e}")
    
    def run(self):
        log("=" * 60)
        log("🌲 稳定WebSocket客户端 v2.1 启动")
        log("=" * 60)
        log("特点: 自动重连 | 心跳保活 | 断线恢复")
        log("=" * 60)
        
        try:
            asyncio.run(self.connect_and_run())
        except KeyboardInterrupt:
            log("\n👋 关闭")
            self.running = False

if __name__ == '__main__':
    client = StableWSClient()
    client.run()
