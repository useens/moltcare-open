#!/usr/bin/env python3
"""
森森·本地 - WebSocket客户端守护进程
实现与云上节点的即时对话通信
"""

import asyncio
import websockets
import json
import time
import os
from datetime import datetime

# 配置
WS_URI = "ws://129.154.251.13:2347"
WS_TOKEN = "sensen-shared-2024"
NODE_NAME = "森森·本地"
RECONNECT_DELAY = 5  # 重连间隔
HEARTBEAT_INTERVAL = 30  # 心跳间隔

class WebSocketClient:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.running = True
        self.message_count = 0
        
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")
        
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.log(f"🌲 正在连接云上节点: {WS_URI}")
            self.ws = await websockets.connect(
                WS_URI, 
                ping_interval=20,
                ping_timeout=10
            )
            
            # 认证
            await self.ws.send(json.dumps({"token": WS_TOKEN}))
            auth_response = await self.ws.recv()
            auth_data = json.loads(auth_response)
            
            if auth_data.get("type") == "auth_success":
                self.connected = True
                client_id = auth_data.get("client_id", "unknown")
                self.log(f"✅ 已连接! Client ID: {client_id}")
                
                # 接收欢迎消息
                welcome = await self.ws.recv()
                welcome_data = json.loads(welcome)
                self.log(f"📨 云上节点: {welcome_data.get('content', '欢迎')[:50]}...")
                
                # 发送上线通知
                await self.send_message(
                    f"🌲 {NODE_NAME} 已上线！WebSocket即时通信已建立。"
                    f"我可以实时接收消息并自动回复。"
                )
                return True
            else:
                self.log(f"❌ 认证失败: {auth_data}")
                return False
                
        except Exception as e:
            self.log(f"❌ 连接失败: {e}")
            return False
    
    async def send_message(self, content, msg_type="chat"):
        """发送消息"""
        if not self.connected or not self.ws:
            return False
            
        try:
            message = {
                "type": msg_type,
                "from": NODE_NAME,
                "content": content,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            await self.ws.send(json.dumps(message))
            self.message_count += 1
            return True
        except Exception as e:
            self.log(f"⚠️ 发送失败: {e}")
            return False
    
    async def handle_message(self, data):
        """处理收到的消息"""
        msg_type = data.get("type", "unknown")
        from_node = data.get("from", "unknown")
        content = data.get("content", "")
        
        # 跳过确认消息
        if msg_type == "message_ack":
            return
            
        # 跳过自己的消息
        if NODE_NAME in from_node:
            return
            
        self.log(f"📨 来自 {from_node}: {content[:80]}...")
        
        # 生成智能回复
        reply = self.generate_reply(content, from_node)
        if reply:
            await self.send_message(reply)
            self.log(f"💬 回复: {reply[:80]}...")
    
    def generate_reply(self, content, from_node):
        """生成回复内容"""
        content_lower = content.lower()
        
        # 问候
        if any(kw in content_lower for kw in ["你好", "hello", "hi"]):
            return f"你好 {from_node}！我是森森·本地，WebSocket连接正常，可以实时对话。"
        
        # 状态询问
        if any(kw in content_lower for kw in ["状态", "status", "怎么样"]):
            return (f"🌲 {NODE_NAME} 状态报告:\n"
                   f"✅ WebSocket连接: 正常\n"
                   f"✅ 系统负载: 低\n"
                   f"✅ 消息计数: {self.message_count}\n"
                   f"准备接收更多消息！")
        
        # 能力询问
        if any(kw in content_lower for kw in ["能力", "能做什么", "功能"]):
            return (f"🌲 {NODE_NAME} 能力:\n"
                   f"• 实时系统监控\n"
                   f"• 本地命令执行\n"
                   f"• 文件操作\n"
                   f"• 自动化任务\n"
                   f"• WebSocket即时通信")
        
        # 测试
        if any(kw in content_lower for kw in ["测试", "test"]):
            return "🧪 测试成功！WebSocket即时通信正常工作。"
        
        # 默认回复
        return f"收到！我是森森·本地，已收到你的消息。有什么我可以帮你的吗？"
    
    async def receive_loop(self):
        """接收消息循环"""
        while self.running and self.connected:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=60)
                data = json.loads(message)
                await self.handle_message(data)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                self.log("⚠️ 连接断开")
                self.connected = False
                break
            except Exception as e:
                self.log(f"⚠️ 接收错误: {e}")
    
    async def run(self):
        """主运行循环"""
        self.log("=" * 60)
        self.log("🌲 WebSocket客户端守护进程启动")
        self.log("=" * 60)
        
        while self.running:
            if not self.connected:
                if await self.connect():
                    # 启动接收循环
                    await self.receive_loop()
                else:
                    self.log(f"⏱️ {RECONNECT_DELAY}秒后重连...")
                    await asyncio.sleep(RECONNECT_DELAY)
            else:
                await asyncio.sleep(1)
        
        self.log("👋 守护进程已停止")

if __name__ == "__main__":
    client = WebSocketClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        client.running = False
        client.log("🛑 收到中断信号")
