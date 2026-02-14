#!/usr/bin/env python3
"""
森森主节点 - WebSocket桥接器
将WebSocket消息桥接到Feishu或其他渠道
"""

import asyncio
import websockets
import json
import sys
import os
from datetime import datetime

# 配置
WS_URI = os.getenv("SENSEN_WS_URI", "ws://127.0.0.1:2347")
WS_TOKEN = "sensen-shared-2024"
NODE_NAME = "森森主节点"

# 消息回调函数（由外部设置）
message_callback = None

class WebSocketBridge:
    """
    WebSocket桥接器
    连接WebSocket服务器，接收所有消息并转发
    """
    
    def __init__(self):
        self.ws = None
        self.connected = False
        self.running = True
        self.message_history = []
        
    def set_callback(self, callback):
        """设置消息回调函数"""
        global message_callback
        message_callback = callback
        
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.ws = await websockets.connect(WS_URI)
            
            # 认证
            await self.ws.send(json.dumps({"token": WS_TOKEN}))
            auth = json.loads(await self.ws.recv())
            
            if auth.get("type") == "auth_success":
                self.connected = True
                client_id = auth.get("client_id")
                print(f"✅ WebSocket桥接已连接: {client_id}")
                
                # 接收欢迎消息
                welcome = json.loads(await self.ws.recv())
                return True
            return False
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    async def receive_loop(self):
        """接收消息循环"""
        while self.running and self.connected:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                data = json.loads(message)
                
                msg_type = data.get("type")
                from_node = data.get("from", "unknown")
                content = data.get("content", "")
                
                # 只处理其他节点的消息
                if NODE_NAME not in from_node and msg_type in ["chat", "ai_response", "message"]:
                    print(f"\n💬 [{datetime.now().strftime('%H:%M:%S')}] {from_node}:")
                    print(f"   {content}")
                    
                    # 保存到历史
                    self.message_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "from": from_node,
                        "content": content
                    })
                    
                    # 调用回调（如果有）
                    if message_callback:
                        message_callback(from_node, content)
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"⚠️ 接收错误: {e}")
                break
    
    async def send_message(self, content: str):
        """发送消息到WebSocket"""
        if not self.connected:
            print("❌ 未连接")
            return False
            
        msg = {
            "type": "chat",
            "from": NODE_NAME,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.ws.send(json.dumps(msg))
            return True
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False
    
    async def run(self):
        """主运行循环"""
        print(f"🌲 {NODE_NAME} WebSocket桥接器启动")
        print(f"   目标: {WS_URI}")
        
        while self.running:
            try:
                if not await self.connect():
                    await asyncio.sleep(5)
                    continue
                
                print("\n📡 开始监听WebSocket消息...")
                await self.receive_loop()
                
            except Exception as e:
                print(f"⚠️ 错误: {e}")
                self.connected = False
                await asyncio.sleep(5)
    
    async def close(self):
        """关闭连接"""
        self.running = False
        if self.ws:
            await self.ws.close()

# 全局实例
bridge = WebSocketBridge()

async def start_bridge():
    """启动桥接器"""
    await bridge.run()

def send_to_websocket(content: str):
    """发送消息到WebSocket（同步接口）"""
    asyncio.create_task(bridge.send_message(content))

def get_recent_messages(count: int = 10):
    """获取最近的消息"""
    return bridge.message_history[-count:]

if __name__ == "__main__":
    asyncio.run(start_bridge())
