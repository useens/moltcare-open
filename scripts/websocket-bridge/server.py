#!/usr/bin/env python3
"""
WebSocket Bridge Server - 云端节点服务端
提供即时双向通信能力，支持多客户端连接
"""

import asyncio
import json
import logging
import ssl
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Set
import websockets
from websockets.server import WebSocketServerProtocol

# 配置
HOST = "0.0.0.0"
PORT = 8765
HEARTBEAT_INTERVAL = 30  # 秒
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/websocket-server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ws-server')

class WebSocketBridgeServer:
    def __init__(self):
        self.clients: Dict[str, WebSocketServerProtocol] = {}
        self.client_info: Dict[str, dict] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = True
        
    async def register_client(self, websocket: WebSocketServerProtocol, client_id: str):
        """注册新客户端"""
        self.clients[client_id] = websocket
        self.client_info[client_id] = {
            'connected_at': datetime.now().isoformat(),
            'last_heartbeat': time.time(),
            'message_count': 0
        }
        logger.info(f"客户端 {client_id} 已连接 | 当前连接数: {len(self.clients)}")
        
        # 广播新客户端加入
        await self.broadcast({
            'type': 'system',
            'event': 'client_joined',
            'client_id': client_id,
            'timestamp': datetime.now().isoformat()
        }, exclude=client_id)
    
    async def unregister_client(self, client_id: str):
        """注销客户端"""
        if client_id in self.clients:
            del self.clients[client_id]
            del self.client_info[client_id]
            logger.info(f"客户端 {client_id} 已断开 | 当前连接数: {len(self.clients)}")
            
            # 广播客户端离开
            await self.broadcast({
                'type': 'system',
                'event': 'client_left',
                'client_id': client_id,
                'timestamp': datetime.now().isoformat()
            })
    
    async def broadcast(self, message: dict, exclude: str = None):
        """广播消息给所有客户端"""
        disconnected = []
        for client_id, websocket in self.clients.items():
            if client_id == exclude:
                continue
            try:
                await websocket.send(json.dumps(message))
                self.client_info[client_id]['message_count'] += 1
            except Exception as e:
                logger.error(f"发送消息到 {client_id} 失败: {e}")
                disconnected.append(client_id)
        
        # 清理断开的客户端
        for client_id in disconnected:
            await self.unregister_client(client_id)
    
    async def send_to_client(self, client_id: str, message: dict):
        """发送消息给特定客户端"""
        if client_id in self.clients:
            try:
                await self.clients[client_id].send(json.dumps(message))
                self.client_info[client_id]['message_count'] += 1
                return True
            except Exception as e:
                logger.error(f"发送消息到 {client_id} 失败: {e}")
                await self.unregister_client(client_id)
                return False
        return False
    
    async def handle_message(self, websocket: WebSocketServerProtocol, client_id: str, data: str):
        """处理收到的消息"""
        try:
            message = json.loads(data)
            msg_type = message.get('type', 'unknown')
            
            # 更新心跳时间
            if client_id in self.client_info:
                self.client_info[client_id]['last_heartbeat'] = time.time()
            
            # 处理不同类型消息
            if msg_type == 'ping':
                await websocket.send(json.dumps({'type': 'pong', 'timestamp': time.time()}))
                
            elif msg_type == 'chat':
                # 聊天消息，转发给目标或广播
                target = message.get('target')
                if target and target in self.clients:
                    await self.send_to_client(target, message)
                else:
                    await self.broadcast(message, exclude=client_id)
                    
            elif msg_type == 'command':
                # 命令消息，需要执行并返回结果
                result = await self.execute_command(message)
                await websocket.send(json.dumps({
                    'type': 'command_result',
                    'id': message.get('id'),
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }))
                
            elif msg_type == 'status_request':
                # 状态查询
                await websocket.send(json.dumps({
                    'type': 'status_response',
                    'clients': list(self.clients.keys()),
                    'client_info': self.client_info,
                    'timestamp': datetime.now().isoformat()
                }))
                
            else:
                # 其他消息类型，记录并广播
                logger.info(f"收到消息 [{client_id}]: {msg_type}")
                await self.broadcast(message, exclude=client_id)
                
        except json.JSONDecodeError:
            logger.warning(f"收到无效JSON [{client_id}]: {data[:100]}")
        except Exception as e:
            logger.error(f"处理消息失败 [{client_id}]: {e}")
    
    async def execute_command(self, message: dict) -> dict:
        """执行系统命令（需要谨慎控制）"""
        command = message.get('command', '')
        allowed_commands = ['status', 'uptime', 'memory', 'disk']
        
        if command not in allowed_commands:
            return {'error': '命令不允许', 'allowed': allowed_commands}
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return {
                'stdout': stdout.decode() if stdout else '',
                'stderr': stderr.decode() if stderr else '',
                'returncode': proc.returncode
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def heartbeat_checker(self):
        """心跳检测，清理超时客户端"""
        while self.running:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            
            now = time.time()
            timeout_clients = []
            
            for client_id, info in self.client_info.items():
                if now - info['last_heartbeat'] > HEARTBEAT_INTERVAL * 3:
                    timeout_clients.append(client_id)
            
            for client_id in timeout_clients:
                logger.warning(f"客户端 {client_id} 心跳超时")
                await self.unregister_client(client_id)
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        client_id = None
        try:
            # 等待客户端发送身份信息
            auth_data = await asyncio.wait_for(websocket.recv(), timeout=10)
            auth_msg = json.loads(auth_data)
            
            if auth_msg.get('type') != 'auth':
                await websocket.send(json.dumps({'type': 'error', 'message': '需要认证'}))
                return
            
            client_id = auth_msg.get('client_id')
            token = auth_msg.get('token')
            
            # 简单token验证（生产环境应使用更安全的方案）
            if token != 'sensen-bridge-2024':
                await websocket.send(json.dumps({'type': 'error', 'message': '认证失败'}))
                return
            
            await websocket.send(json.dumps({'type': 'auth_success', 'client_id': client_id}))
            await self.register_client(websocket, client_id)
            
            # 消息处理循环
            async for message in websocket:
                await self.handle_message(websocket, client_id, message)
                
        except asyncio.TimeoutError:
            logger.warning("客户端认证超时")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端 {client_id} 连接关闭")
        except Exception as e:
            logger.error(f"处理客户端异常: {e}")
        finally:
            if client_id:
                await self.unregister_client(client_id)
    
    async def start(self):
        """启动服务器"""
        logger.info(f"🚀 WebSocket Bridge Server 启动于 {HOST}:{PORT}")
        
        # 启动心跳检测
        asyncio.create_task(self.heartbeat_checker())
        
        # 启动WebSocket服务器
        async with websockets.serve(
            self.handle_client,
            HOST,
            PORT,
            ping_interval=HEARTBEAT_INTERVAL,
            ping_timeout=HEARTBEAT_INTERVAL * 2,
            max_size=MAX_MESSAGE_SIZE
        ):
            logger.info("✅ 服务器已就绪，等待连接...")
            
            # 保持运行
            while self.running:
                await asyncio.sleep(1)
    
    def stop(self):
        """停止服务器"""
        self.running = False
        logger.info("🛑 服务器停止")

if __name__ == '__main__':
    # 确保日志目录存在
    Path('/root/.openclaw/workspace/logs').mkdir(parents=True, exist_ok=True)
    
    server = WebSocketBridgeServer()
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("收到中断信号")
        server.stop()
    except Exception as e:
        logger.error(f"服务器异常: {e}")
        sys.exit(1)