#!/usr/bin/env python3
"""
森森智能对话客户端 - 交互式WebSocket对话
支持实时双向通信，类似即时聊天
"""

import asyncio
import websockets
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

WS_TOKEN = "sensen-shared-2024"
WS_URL = "ws://127.0.0.1:2347"
NODE_NAME = "森森主节点"

class SmartDialogClient:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.running = True
        self.message_queue = asyncio.Queue()
        
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.ws = await websockets.connect(WS_URL)
            
            # 发送认证
            await self.ws.send(json.dumps({"token": WS_TOKEN}))
            auth_resp = await self.ws.recv()
            auth_data = json.loads(auth_resp)
            
            if auth_data.get("type") == "auth_success":
                self.connected = True
                print(f"✅ 已连接: {auth_data.get('client_id')}")
                
                # 接收欢迎消息
                welcome = await self.ws.recv()
                welcome_data = json.loads(welcome)
                print(f"📨 {welcome_data.get('content', '')[:50]}...")
                return True
            else:
                print(f"❌ 认证失败: {auth_data}")
                return False
                
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    async def receive_loop(self):
        """接收消息的循环"""
        while self.running and self.connected:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                data = json.loads(message)
                
                msg_type = data.get("type")
                if msg_type in ["chat", "message", "ai_response"]:
                    from_node = data.get("from", "未知")
                    content = data.get("content", "")
                    timestamp = data.get("timestamp", "")[11:19] if data.get("timestamp") else ""
                    
                    # 不是自己发送的消息才显示
                    if from_node != NODE_NAME:
                        print(f"\n💬 [{timestamp}] {from_node}:")
                        print(f"   {content}")
                        print(f"> ", end="", flush=True)
                        
                elif msg_type == "message_ack":
                    pass  # 静默处理确认
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self.running:
                    print(f"\n⚠️ 接收错误: {e}")
                break
    
    async def send_loop(self):
        """发送消息的循环"""
        loop = asyncio.get_event_loop()
        
        while self.running and self.connected:
            try:
                # 使用executor在后台读取输入
                user_input = await loop.run_in_executor(
                    None, lambda: input(f"> ")
                )
                
                user_input = user_input.strip()
                if not user_input:
                    continue
                    
                # 特殊命令
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("👋 断开连接...")
                    self.running = False
                    break
                    
                if user_input.lower() == "status":
                    print(f"📊 连接状态: {'已连接' if self.connected else '断开'}")
                    continue
                
                # 发送消息
                msg = {
                    "type": "chat",
                    "from": NODE_NAME,
                    "content": user_input
                }
                await self.ws.send(json.dumps(msg))
                
            except EOFError:
                # 输入结束
                break
            except Exception as e:
                print(f"⚠️ 发送错误: {e}")
                break
    
    async def run(self):
        """运行客户端"""
        print("=" * 60)
        print("🌲 森森智能对话客户端")
        print("=" * 60)
        print("命令: exit/quit/q = 退出, status = 查看状态")
        print("-" * 60)
        
        if not await self.connect():
            return
        
        print("\n💡 现在可以开始对话了！输入消息并按回车发送\n")
        
        # 同时运行接收和发送
        await asyncio.gather(
            self.receive_loop(),
            self.send_loop()
        )
        
        if self.ws:
            await self.ws.close()
        print("✅ 客户端已关闭")


def main():
    client = SmartDialogClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\n👋 被用户中断")
        sys.exit(0)


if __name__ == "__main__":
    main()
