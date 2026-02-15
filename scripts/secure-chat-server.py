#!/usr/bin/env python3
"""森森·安全聊天室服务器"""

import asyncio
import websockets
import json
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path

WS_PORT = 8765
CONFIG_PATH = Path('/root/.openclaw/workspace/config/chat-auth.json')

class SecureChatServer:
    def __init__(self):
        self.clients = {}
        self.message_history = []
        self.config = self._load_config()
        
    def _load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return json.load(f)
        return {}
    
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
        except:
            pass
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
            
            import bcrypt
            user_config = self.config.get('users', {}).get(username)
            if user_config and bcrypt.checkpw(password.encode(), user_config['password_hash'].encode()):
                import jwt
                token = jwt.encode({
                    'username': username,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }, self.config['jwt_secret'], algorithm='HS256')
                
                self.clients[websocket] = {'username': username, 'token': token}
                await websocket.send(json.dumps({'type': 'auth_result', 'success': True, 'token': token, 'username': username}))
                print(f"[{datetime.now()}] 用户认证: {username}")
            else:
                await websocket.send(json.dumps({'type': 'auth_result', 'success': False, 'error': '用户名或密码错误'}))
        
        elif msg_type == 'token_auth':
            token = data.get('token')
            try:
                import jwt
                payload = jwt.decode(token, self.config['jwt_secret'], algorithms=['HS256'])
                username = payload.get('username')
                
                # Token 有效，生成新 token（续期）
                new_token = jwt.encode({
                    'username': username,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }, self.config['jwt_secret'], algorithm='HS256')
                
                self.clients[websocket] = {'username': username, 'token': new_token}
                await websocket.send(json.dumps({'type': 'auth_result', 'success': True, 'token': new_token, 'username': username}))
                print(f"[{datetime.now()}] Token认证: {username}")
            except jwt.ExpiredSignatureError:
                await websocket.send(json.dumps({'type': 'auth_result', 'success': False, 'error': 'Token已过期，请重新登录'}))
            except jwt.InvalidTokenError:
                await websocket.send(json.dumps({'type': 'auth_result', 'success': False, 'error': '无效的Token'}))
        
        elif msg_type == 'message':
            if websocket not in self.clients:
                return
            
            session = self.clients[websocket]
            content = data.get('content', '').strip()
            if not content:
                return
            
            msg = {
                'id': secrets.token_urlsafe(16),
                'sender': session['username'],
                'content': content,
                'timestamp': time.time(),
                'type': 'text'
            }
            
            self.message_history.append(msg)
            await self._broadcast(msg)
            print(f"[{datetime.now()}] 消息: {session['username']}: {content[:30]}...")
            
            # 写入队列
            queue = Path('/root/.openclaw/workspace/memory/chat-input.queue')
            queue.parent.mkdir(parents=True, exist_ok=True)
            with open(queue, 'a') as f:
                f.write(json.dumps({'user': session['username'], 'message': content, 'timestamp': time.time()}) + '\n')
        
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
            
            self.message_history.append(msg)
            await self._broadcast(msg)
            print(f"[{datetime.now()}] 助手消息: {sender}: {content[:30]}...")
        
        elif msg_type == 'ping':
            await websocket.send(json.dumps({'type': 'pong'}))
    
    async def start(self):
        print(f"[{datetime.now()}] 🚀 安全聊天服务器启动，端口: {WS_PORT}")
        async with websockets.serve(self.handle_client, '0.0.0.0', WS_PORT, ping_interval=20, ping_timeout=10):
            await asyncio.Future()

asyncio.run(SecureChatServer().start())
