#!/usr/bin/env python3
"""森森·安全聊天室服务器 - 简化版"""

import asyncio
import websockets
import json
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path

WS_PORT = 8765

class ChatServer:
    def __init__(self):
        self.clients = {}
        self.message_history = []
        
    async def _broadcast(self, message, exclude=None):
        disconnected = []
        for client, session in self.clients.items():
            if client != exclude:
                try:
                    await client.send(json.dumps(message))
                except:
                    disconnected.append(client)
        
        for client in disconnected:
            if client in self.clients:
                del self.clients[client]
    
    async def handle_client(self, websocket, path=None):
        client_ip = websocket.remote_address[0]
        print(f"[{datetime.now()}] 新连接: {client_ip}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data, client_ip)
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"[{datetime.now()}] 连接错误: {e}")
        finally:
            if websocket in self.clients:
                user = self.clients[websocket]['username']
                del self.clients[websocket]
                print(f"[{datetime.now()}] 用户断开: {user}")
    
    async def _handle_message(self, websocket, data, client_ip):
        msg_type = data.get('type')
        
        if msg_type == 'auth':
            username = data.get('username')
            password = data.get('password')
            
            # 简单认证：admin/sen666 或 assistant/assistant_secret_key_2024
            valid = False
            if username == 'admin' and password == 'sen666':
                valid = True
            elif username == 'assistant' and password == 'assistant_secret_key_2024':
                valid = True
            
            if valid:
                self.clients[websocket] = {'username': username}
                await websocket.send(json.dumps({
                    'type': 'auth_result', 
                    'success': True, 
                    'username': username
                }))
                print(f"[{datetime.now()}] 用户认证: {username}")
            else:
                await websocket.send(json.dumps({
                    'type': 'auth_result', 
                    'success': False, 
                    'error': '用户名或密码错误'
                }))
        
        elif msg_type == 'message':
            if websocket not in self.clients:
                return
            
            session = self.clients[websocket]
            content = data.get('content', '').strip()
            if not content:
                return
            
            # 广播用户消息
            msg = {
                'id': secrets.token_urlsafe(16),
                'sender': session['username'],
                'content': content,
                'timestamp': time.time(),
                'type': 'text'
            }
            await self._broadcast(msg)
            print(f"[{datetime.now()}] 消息: {session['username']}: {content[:30]}...")
            
            # 自动回复
            reply_content = None
            if '你好' in content:
                reply_content = '🌲 你好！我是森森，你的数字分身。有什么可以帮你的吗？'
            elif content in ['?', '？']:
                reply_content = '🌲 有什么问题尽管问，我会尽力帮你！'
            elif content in ['1', '111', 'test', '测试']:
                reply_content = '🌲 收到测试消息！聊天室连接正常✅'
            elif '谁' in content or '你是' in content:
                reply_content = '🌲 我是森森（Sensen），你的数字分身！'
            
            if reply_content:
                await asyncio.sleep(0.3)
                reply_msg = {
                    'id': secrets.token_urlsafe(16),
                    'sender': '森森',
                    'content': reply_content,
                    'timestamp': time.time(),
                    'type': 'assistant'
                }
                await self._broadcast(reply_msg)
                print(f"[{datetime.now()}] 自动回复: {reply_content[:30]}...")
        
        elif msg_type == 'assistant_message':
            content = data.get('content', '').strip()
            sender = data.get('sender', '森森')
            if not content:
                return
            
            msg = {
                'id': secrets.token_urlsafe(16),
                'sender': sender,
                'content': content,
                'timestamp': time.time(),
                'type': 'assistant'
            }
            await self._broadcast(msg)
            print(f"[{datetime.now()}] 助手消息: {sender}: {content[:30]}...")
        
        elif msg_type == 'ping':
            await websocket.send(json.dumps({'type': 'pong'}))
    
    async def start(self):
        print(f"[{datetime.now()}] 🚀 聊天服务器启动，端口: {WS_PORT}")
        async with websockets.serve(
            self.handle_client, 
            '0.0.0.0', 
            WS_PORT, 
            ping_interval=20, 
            ping_timeout=10
        ):
            await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(ChatServer().start())
