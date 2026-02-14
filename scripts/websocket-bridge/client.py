#!/usr/bin/env python3
"""
WebSocket Bridge Client - 本地节点客户端
连接到云端服务端，实现即时双向通信
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
import websockets
from websockets.client import WebSocketClientProtocol

# 配置
SERVER_URI = "wss://your-cloud-server:8765"  # 需要替换为实际服务器地址
CLIENT_ID = "sensen-local"  # 本地节点标识
TOKEN = "sensen-bridge-2024"
HEARTBEAT_INTERVAL = 30  # 秒
RECONNECT_DELAY = 5  # 初始重连延迟（秒）
MAX_RECONNECT_DELAY = 300  # 最大重连延迟（秒）

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/websocket-client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ws-client')

class WebSocketBridgeClient:
    def __init__(self):
        self.websocket: WebSocketClientProtocol = None
        self.connected = False
        self.reconnect_delay = RECONNECT_DELAY
        self.message_handlers = {}
        self.running = True
        
        # 注册消息处理器
        self.register_handler('chat', self.handle_chat)
        self.register_handler('command', self.handle_command)
        self.register_handler('system', self.handle_system)
    
    def register_handler(self, msg_type: str, handler):
        """注册消息处理器"""
        self.message_handlers[msg_type] = handler
    
    async def connect(self):
        """连接到服务器"""
        try:
            logger.info(f"正在连接服务器: {SERVER_URI}")
            
            self.websocket = await websockets.connect(
                SERVER_URI,
                ping_interval=HEARTBEAT_INTERVAL,
                ping_timeout=HEARTBEAT_INTERVAL * 2
            )
            
            # 发送认证信息
            auth_msg = {
                'type': 'auth',
                'client_id': CLIENT_ID,
                'token': TOKEN,
                'timestamp': datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(auth_msg))
            
            # 等待认证响应
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            resp_data = json.loads(response)
            
            if resp_data.get('type') == 'auth_success':
                self.connected = True
                self.reconnect_delay = RECONNECT_DELAY  # 重置重连延迟
                logger.info("✅ 认证成功，已连接到服务器")
                return True
            else:
                logger.error(f"认证失败: {resp_data}")
                return False
                
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
        self.connected = False
        logger.info("已断开连接")
    
    async def reconnect(self):
        """重连逻辑（指数退避）"""
        while self.running and not self.connected:
            logger.info(f"{self.reconnect_delay}秒后重连...")
            await asyncio.sleep(self.reconnect_delay)
            
            if await self.connect():
                break
            
            # 指数退避
            self.reconnect_delay = min(self.reconnect_delay * 2, MAX_RECONNECT_DELAY)
    
    async def send(self, message: dict):
        """发送消息"""
        if self.connected and self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                self.connected = False
                return False
        return False
    
    async def send_chat(self, content: str, target: str = None):
        """发送聊天消息"""
        return await self.send({
            'type': 'chat',
            'from': CLIENT_ID,
            'target': target,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
    
    async def send_command(self, command: str, params: dict = None):
        """发送命令"""
        return await self.send({
            'type': 'command',
            'id': f"cmd_{int(time.time())}",
            'command': command,
            'params': params or {},
            'timestamp': datetime.now().isoformat()
        })
    
    async def heartbeat(self):
        """心跳保活"""
        while self.running and self.connected:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            if self.connected:
                try:
                    await self.send({'type': 'ping', 'timestamp': time.time()})
                except Exception as e:
                    logger.error(f"心跳失败: {e}")
                    self.connected = False
    
    async def receive_loop(self):
        """接收消息循环"""
        while self.running and self.connected:
            try:
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=HEARTBEAT_INTERVAL * 2
                )
                await self.handle_message(message)
            except asyncio.TimeoutError:
                logger.warning("接收消息超时")
                self.connected = False
            except websockets.exceptions.ConnectionClosed:
                logger.info("连接已关闭")
                self.connected = False
            except Exception as e:
                logger.error(f"接收消息异常: {e}")
                self.connected = False
    
    async def handle_message(self, data: str):
        """处理收到的消息"""
        try:
            message = json.loads(data)
            msg_type = message.get('type', 'unknown')
            
            # 查找对应的处理器
            handler = self.message_handlers.get(msg_type)
            if handler:
                await handler(message)
            else:
                logger.info(f"收到消息 [{msg_type}]: {message}")
                
        except json.JSONDecodeError:
            logger.warning(f"收到无效JSON: {data[:100]}")
    
    async def handle_chat(self, message: dict):
        """处理聊天消息"""
        from_client = message.get('from', 'unknown')
        content = message.get('content', '')
        
        logger.info(f"💬 [{from_client}]: {content}")
        
        # 自动回复示例（实际可接入AI处理）
        if from_client != CLIENT_ID:
            # 这里可以接入AI生成回复
            response = f"收到消息: {content[:50]}..."
            await self.send_chat(response, target=from_client)
    
    async def handle_command(self, message: dict):
        """处理命令"""
        command = message.get('command')
        params = message.get('params', {})
        
        logger.info(f"⚡ 执行命令: {command}")
        
        # 执行本地命令
        result = await self.execute_local_command(command, params)
        
        # 发送结果
        await self.send({
            'type': 'command_result',
            'id': message.get('id'),
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    
    async def handle_system(self, message: dict):
        """处理系统消息"""
        event = message.get('event')
        logger.info(f"🔔 系统事件: {event}")
        
        if event == 'client_joined':
            client_id = message.get('client_id')
            logger.info(f"新客户端加入: {client_id}")
        elif event == 'client_left':
            client_id = message.get('client_id')
            logger.info(f"客户端离开: {client_id}")
    
    async def execute_local_command(self, command: str, params: dict) -> dict:
        """执行本地命令"""
        try:
            if command == 'status':
                return {
                    'client_id': CLIENT_ID,
                    'status': 'running',
                    'uptime': time.time(),  # 简化处理
                    'timestamp': datetime.now().isoformat()
                }
            elif command == 'memory':
                import psutil
                mem = psutil.virtual_memory()
                return {
                    'total': mem.total,
                    'available': mem.available,
                    'percent': mem.percent
                }
            elif command == 'disk':
                import psutil
                disk = psutil.disk_usage('/')
                return {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                }
            else:
                return {'error': f'未知命令: {command}'}
        except Exception as e:
            return {'error': str(e)}
    
    async def run(self):
        """主运行循环"""
        logger.info("🚀 WebSocket Bridge Client 启动")
        
        while self.running:
            if not self.connected:
                if await self.connect():
                    # 启动并发的接收和心跳任务
                    await asyncio.gather(
                        self.receive_loop(),
                        self.heartbeat(),
                        return_exceptions=True
                    )
                else:
                    await self.reconnect()
            else:
                await asyncio.sleep(1)
    
    def stop(self):
        """停止客户端"""
        self.running = False
        asyncio.create_task(self.disconnect())
        logger.info("🛑 客户端停止")

if __name__ == '__main__':
    # 确保日志目录存在
    Path('/root/.openclaw/workspace/logs').mkdir(parents=True, exist_ok=True)
    
    client = WebSocketBridgeClient()
    
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logger.info("收到中断信号")
        client.stop()
    except Exception as e:
        logger.error(f"客户端异常: {e}")
        sys.exit(1)