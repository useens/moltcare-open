#!/usr/bin/env python3
"""
WebSocket Server - 云端节点服务端
实现高可靠性、带认证和心跳管理的WebSocket服务器
"""

import asyncio
import json
import logging
import ssl
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Set
from collections import defaultdict

import websockets
from websockets.server import WebSocketServerProtocol

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('websocket-server')


@dataclass
class ConnectionInfo:
    """连接信息"""
    node_id: str
    node_type: str
    connected_at: float
    last_heartbeat: float
    session_id: str
    capabilities: list = field(default_factory=list)
    websocket: Optional[WebSocketServerProtocol] = None
    authenticated: bool = False


class MessageProtocol:
    """消息协议处理器"""
    
    @staticmethod
    def create_message(
        msg_type: str,
        sender: str,
        receiver: str,
        payload: dict,
        msg_id: Optional[str] = None
    ) -> dict:
        """创建标准消息格式"""
        return {
            "msg_id": msg_id or str(uuid.uuid4()),
            "msg_type": msg_type,
            "timestamp": int(time.time()),
            "sender": sender,
            "receiver": receiver,
            "payload": payload
        }
    
    @staticmethod
    def parse_message(data: str) -> Optional[dict]:
        """解析消息"""
        try:
            msg = json.loads(data)
            required = ["msg_id", "msg_type", "timestamp", "sender", "receiver", "payload"]
            if all(k in msg for k in required):
                return msg
            logger.warning(f"消息缺少必要字段: {msg}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return None


class ConnectionManager:
    """连接管理器"""
    
    def __init__(self, heartbeat_timeout: int = 90):
        self.connections: Dict[str, ConnectionInfo] = {}  # session_id -> info
        self.node_connections: Dict[str, str] = {}  # node_id -> session_id
        self.heartbeat_timeout = heartbeat_timeout
        self._lock = asyncio.Lock()
    
    async def add_connection(
        self,
        node_id: str,
        node_type: str,
        capabilities: list,
        websocket: WebSocketServerProtocol
    ) -> ConnectionInfo:
        """添加新连接"""
        async with self._lock:
            # 如果节点已存在连接，踢除旧连接
            if node_id in self.node_connections:
                old_session = self.node_connections[node_id]
                if old_session in self.connections:
                    old_info = self.connections[old_session]
                    logger.info(f"踢除旧连接: {node_id}, session={old_session}")
                    try:
                        await old_info.websocket.close(1008, "New connection established")
                    except:
                        pass
                    del self.connections[old_session]
            
            session_id = str(uuid.uuid4())
            now = time.time()
            info = ConnectionInfo(
                node_id=node_id,
                node_type=node_type,
                connected_at=now,
                last_heartbeat=now,
                session_id=session_id,
                capabilities=capabilities,
                websocket=websocket,
                authenticated=True
            )
            
            self.connections[session_id] = info
            self.node_connections[node_id] = session_id
            logger.info(f"新连接: {node_id}, session={session_id}")
            return info
    
    async def remove_connection(self, session_id: str):
        """移除连接"""
        async with self._lock:
            if session_id in self.connections:
                info = self.connections[session_id]
                del self.connections[session_id]
                if info.node_id in self.node_connections:
                    if self.node_connections[info.node_id] == session_id:
                        del self.node_connections[info.node_id]
                logger.info(f"连接断开: {info.node_id}, session={session_id}")
    
    async def update_heartbeat(self, session_id: str) -> bool:
        """更新心跳时间"""
        async with self._lock:
            if session_id in self.connections:
                self.connections[session_id].last_heartbeat = time.time()
                return True
            return False
    
    async def get_connection(self, node_id: str) -> Optional[ConnectionInfo]:
        """获取节点连接信息"""
        async with self._lock:
            if node_id in self.node_connections:
                session_id = self.node_connections[node_id]
                return self.connections.get(session_id)
            return None
    
    async def get_all_connections(self) -> Dict[str, ConnectionInfo]:
        """获取所有连接"""
        async with self._lock:
            return dict(self.connections)
    
    async def check_timeouts(self) -> list:
        """检查超时的连接"""
        async with self._lock:
            now = time.time()
            timeouts = []
            for session_id, info in list(self.connections.items()):
                if now - info.last_heartbeat > self.heartbeat_timeout:
                    timeouts.append(session_id)
            return timeouts


class AuthManager:
    """认证管理器"""
    
    def __init__(self, valid_tokens: Optional[Set[str]] = None):
        # 简单的token集合，生产环境应使用数据库存储或JWT验证
        self.valid_tokens = valid_tokens or {"demo-token-12345", "test-token-67890"}
    
    def validate_token(self, token: str) -> bool:
        """验证token"""
        # 简单的token验证，实际应实现JWT验证或数据库查询
        return token in self.valid_tokens or token.startswith("valid-")
    
    def generate_token(self, node_id: str) -> str:
        """生成token (仅用于测试)"""
        return f"valid-{node_id}-{int(time.time())}"


class MessageHandler:
    """消息处理器"""
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        auth_manager: AuthManager
    ):
        self.cm = connection_manager
        self.am = auth_manager
        self.protocol = MessageProtocol()
        self.request_handlers: Dict[str, Callable] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """设置默认处理器"""
        self.register_request_handler("get_status", self._handle_get_status)
        self.register_request_handler("ping", self._handle_ping)
        self.register_request_handler("echo", self._handle_echo)
    
    def register_request_handler(self, action: str, handler: Callable):
        """注册请求处理器"""
        self.request_handlers[action] = handler
    
    async def handle_auth(
        self,
        websocket: WebSocketServerProtocol,
        message: dict
    ) -> Optional[ConnectionInfo]:
        """处理认证消息"""
        payload = message.get("payload", {})
        token = payload.get("token", "")
        node_id = message.get("sender", "")
        node_type = payload.get("node_type", "unknown")
        capabilities = payload.get("capabilities", [])
        
        if not self.am.validate_token(token):
            response = self.protocol.create_message(
                "auth_response",
                "cloud-server",
                node_id,
                {"success": False, "error": "Invalid token"}
            )
            await websocket.send(json.dumps(response))
            return None
        
        # 添加连接
        info = await self.cm.add_connection(
            node_id, node_type, capabilities, websocket
        )
        
        # 发送认证成功响应
        response = self.protocol.create_message(
            "auth_response",
            "cloud-server",
            node_id,
            {
                "success": True,
                "session_id": info.session_id,
                "server_time": int(time.time()),
                "heartbeat_interval": 30
            }
        )
        await websocket.send(json.dumps(response))
        return info
    
    async def handle_heartbeat(
        self,
        session_id: str,
        message: dict
    ):
        """处理心跳消息"""
        success = await self.cm.update_heartbeat(session_id)
        if success:
            payload = message.get("payload", {})
            sequence = payload.get("sequence", 0)
            info = await self.cm.get_all_connections()
            conn_info = info.get(session_id)
            if conn_info:
                response = self.protocol.create_message(
                    "heartbeat_ack",
                    "cloud-server",
                    conn_info.node_id,
                    {"sequence": sequence, "server_time": int(time.time())}
                )
                await conn_info.websocket.send(json.dumps(response))
    
    async def handle_request(
        self,
        session_id: str,
        message: dict
    ):
        """处理业务请求"""
        info = (await self.cm.get_all_connections()).get(session_id)
        if not info:
            return
        
        payload = message.get("payload", {})
        action = payload.get("action", "")
        request_id = payload.get("request_id", "")
        
        handler = self.request_handlers.get(action)
        if handler:
            try:
                result = await handler(payload)
                success = True
                error_code = None
                error_message = None
            except Exception as e:
                result = {}
                success = False
                error_code = "INTERNAL_ERROR"
                error_message = str(e)
                logger.error(f"处理请求 {action} 失败: {e}")
        else:
            result = {}
            success = False
            error_code = "ACTION_NOT_SUPPORTED"
            error_message = f"Unknown action: {action}"
        
        response = self.protocol.create_message(
            "response",
            "cloud-server",
            info.node_id,
            {
                "request_id": request_id,
                "success": success,
                "data": result,
                "error_code": error_code,
                "error_message": error_message
            }
        )
        await info.websocket.send(json.dumps(response))
    
    async def _handle_get_status(self, params: dict) -> dict:
        """处理获取状态请求"""
        return {
            "server_time": int(time.time()),
            "active_connections": len(await self.cm.get_all_connections()),
            "version": "1.0.0"
        }
    
    async def _handle_ping(self, params: dict) -> dict:
        """处理ping请求"""
        return {"pong": True, "timestamp": int(time.time())}
    
    async def _handle_echo(self, params: dict) -> dict:
        """处理echo请求"""
        return {"echo": params.get("message", "")}


class WebSocketServer:
    """WebSocket服务器"""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        ssl_context: Optional[ssl.SSLContext] = None,
        heartbeat_timeout: int = 90
    ):
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.cm = ConnectionManager(heartbeat_timeout)
        self.am = AuthManager()
        self.handler = MessageHandler(self.cm, self.am)
        self.protocol = MessageProtocol()
        self._stop_event = asyncio.Event()
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        session_id = None
        try:
            # 等待认证消息
            auth_timeout = 10.0
            raw_message = await asyncio.wait_for(
                websocket.recv(),
                timeout=auth_timeout
            )
            
            message = self.protocol.parse_message(raw_message)
            if not message:
                await websocket.close(1008, "Invalid message format")
                return
            
            if message.get("msg_type") != "auth":
                await websocket.close(1008, "Expected auth message")
                return
            
            # 处理认证
            info = await self.handler.handle_auth(websocket, message)
            if not info:
                await websocket.close(1008, "Authentication failed")
                return
            
            session_id = info.session_id
            logger.info(f"客户端认证成功: {info.node_id}")
            
            # 处理后续消息
            async for raw_message in websocket:
                message = self.protocol.parse_message(raw_message)
                if not message:
                    continue
                
                msg_type = message.get("msg_type")
                
                if msg_type == "heartbeat":
                    await self.handler.handle_heartbeat(session_id, message)
                elif msg_type == "request":
                    await self.handler.handle_request(session_id, message)
                elif msg_type == "response":
                    # 处理响应（异步请求的响应）
                    logger.debug(f"收到响应: {message}")
                elif msg_type == "event":
                    # 处理事件上报
                    logger.info(f"收到事件: {message}")
                else:
                    logger.warning(f"未知消息类型: {msg_type}")
                    
        except asyncio.TimeoutError:
            logger.warning("认证超时")
            await websocket.close(1008, "Authentication timeout")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"连接关闭: {session_id}")
        except Exception as e:
            logger.error(f"处理客户端异常: {e}")
        finally:
            if session_id:
                await self.cm.remove_connection(session_id)
    
    async def _heartbeat_monitor(self):
        """心跳监控任务"""
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                pass
            
            # 检查超时连接
            timeouts = await self.cm.check_timeouts()
            for session_id in timeouts:
                info = (await self.cm.get_all_connections()).get(session_id)
                if info and info.websocket:
                    logger.warning(f"心跳超时，关闭连接: {info.node_id}")
                    try:
                        await info.websocket.close(1001, "Heartbeat timeout")
                    except:
                        pass
                await self.cm.remove_connection(session_id)
    
    async def start(self):
        """启动服务器"""
        logger.info(f"启动WebSocket服务器: {self.host}:{self.port}")
        
        # 启动心跳监控
        monitor_task = asyncio.create_task(self._heartbeat_monitor())
        
        # 启动WebSocket服务器
        async with websockets.serve(
            self._handle_client,
            self.host,
            self.port,
            ssl=self.ssl_context,
            ping_interval=None,  # 使用应用层心跳
            ping_timeout=None
        ) as server:
            logger.info("WebSocket服务器已启动")
            await self._stop_event.wait()
        
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
    
    def stop(self):
        """停止服务器"""
        logger.info("停止WebSocket服务器")
        self._stop_event.set()


def create_ssl_context(cert_path: str, key_path: str) -> ssl.SSLContext:
    """创建SSL上下文"""
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_path, key_path)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    return ssl_context


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WebSocket Server')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=8765, help='监听端口')
    parser.add_argument('--cert', help='SSL证书路径')
    parser.add_argument('--key', help='SSL密钥路径')
    parser.add_argument('--timeout', type=int, default=90, help='心跳超时(秒)')
    
    args = parser.parse_args()
    
    ssl_context = None
    if args.cert and args.key:
        ssl_context = create_ssl_context(args.cert, args.key)
        logger.info("启用SSL/TLS加密")
    
    server = WebSocketServer(
        host=args.host,
        port=args.port,
        ssl_context=ssl_context,
        heartbeat_timeout=args.timeout
    )
    
    # 信号处理
    loop = asyncio.get_event_loop()
    for sig in ('SIGINT', 'SIGTERM'):
        try:
            loop.add_signal_handler(
                getattr(__import__('signal'), sig),
                server.stop
            )
        except NotImplementedError:
            pass  # Windows不支持
    
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
