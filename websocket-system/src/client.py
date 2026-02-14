#!/usr/bin/env python3
"""
WebSocket Client - 本地节点客户端
实现自动重连、心跳、自动响应的WebSocket客户端
"""

import asyncio
import json
import logging
import random
import ssl
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any, List
from enum import Enum

import websockets
from websockets.client import WebSocketClientProtocol

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('websocket-client')


class ConnectionState(Enum):
    """连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


@dataclass
class ClientConfig:
    """客户端配置"""
    server_url: str = "ws://localhost:8765"
    node_id: str = "local-node-01"
    token: str = "demo-token-12345"
    node_type: str = "local"
    capabilities: List[str] = field(default_factory=lambda: ["sensor", "camera"])
    version: str = "1.0.0"
    
    # 重连配置
    reconnect_enabled: bool = True
    reconnect_base_delay: float = 1.0
    reconnect_max_delay: float = 60.0
    reconnect_max_attempts: int = 0  # 0表示无限重试
    
    # 心跳配置
    heartbeat_interval: int = 30
    heartbeat_timeout: int = 10
    
    # 自动响应配置
    auto_response_enabled: bool = True
    auto_report_enabled: bool = False
    auto_report_interval: int = 300


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
            return json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return None


class ReconnectManager:
    """重连管理器 - 指数退避策略"""
    
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_attempts: int = 0
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self.attempt = 0
        self._last_delay = 0
    
    def reset(self):
        """重置重连计数"""
        self.attempt = 0
        self._last_delay = 0
    
    def get_next_delay(self) -> float:
        """获取下一次重连延迟（指数退避）"""
        if self.max_attempts > 0 and self.attempt >= self.max_attempts:
            raise Exception("达到最大重连次数")
        
        # 指数退避: base * 2^attempt + 随机抖动
        delay = min(
            self.base_delay * (2 ** self.attempt),
            self.max_delay
        )
        # 添加 ±20% 的随机抖动
        jitter = delay * 0.2 * (2 * random.random() - 1)
        delay = delay + jitter
        
        self.attempt += 1
        self._last_delay = delay
        return delay
    
    @property
    def current_attempt(self) -> int:
        return self.attempt


class AutoResponseHandler:
    """自动响应处理器"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.protocol = MessageProtocol()
        self._handlers: Dict[str, Callable] = {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置默认处理器"""
        self._handlers["get_status"] = self._handle_get_status
        self._handlers["ping"] = self._handle_ping
        self._handlers["echo"] = self._handle_echo
        self._handlers["get_sensor_data"] = self._handle_get_sensor_data
        self._handlers["execute_command"] = self._handle_execute_command
    
    async def handle(self, action: str, params: dict) -> dict:
        """处理自动响应"""
        handler = self._handlers.get(action)
        if handler:
            return await handler(params)
        return {"error": f"Action {action} not supported"}
    
    async def _handle_get_status(self, params: dict) -> dict:
        """获取系统状态"""
        import psutil
        return {
            "node_id": self.node_id,
            "timestamp": int(time.time()),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "boot_time": psutil.boot_time()
        }
    
    async def _handle_ping(self, params: dict) -> dict:
        """Ping响应"""
        return {"pong": True, "timestamp": int(time.time())}
    
    async def _handle_echo(self, params: dict) -> dict:
        """Echo响应"""
        return {"echo": params.get("message", "")}
    
    async def _handle_get_sensor_data(self, params: dict) -> dict:
        """获取传感器数据（模拟）"""
        sensor_id = params.get("sensor_id", "default")
        return {
            "sensor_id": sensor_id,
            "value": random.uniform(20.0, 30.0),
            "unit": "celsius",
            "timestamp": int(time.time())
        }
    
    async def _handle_execute_command(self, params: dict) -> dict:
        """执行命令"""
        command = params.get("command", "")
        args = params.get("args", [])
        # 安全限制：只允许特定命令
        allowed_commands = ["uptime", "date", "uname"]
        if command not in allowed_commands:
            return {"error": f"Command {command} not allowed"}
        
        try:
            proc = await asyncio.create_subprocess_exec(
                command, *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return {
                "command": command,
                "returncode": proc.returncode,
                "stdout": stdout.decode().strip(),
                "stderr": stderr.decode().strip()
            }
        except Exception as e:
            return {"error": str(e)}


class WebSocketClient:
    """WebSocket客户端"""
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self.protocol = MessageProtocol()
        self.reconnect_mgr = ReconnectManager(
            base_delay=config.reconnect_base_delay,
            max_delay=config.reconnect_max_delay,
            max_attempts=config.reconnect_max_attempts
        )
        self.auto_handler = AutoResponseHandler(config.node_id)
        
        self.state = ConnectionState.DISCONNECTED
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._auto_report_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._heartbeat_sequence = 0
        self._pending_responses: Dict[str, asyncio.Future] = {}
        
        # SSL上下文
        self.ssl_context: Optional[ssl.SSLContext] = None
        if config.server_url.startswith("wss://"):
            self.ssl_context = ssl.create_default_context()
    
    async def connect(self) -> bool:
        """建立连接"""
        self.state = ConnectionState.CONNECTING
        logger.info(f"连接到服务器: {self.config.server_url}")
        
        try:
            self.websocket = await websockets.connect(
                self.config.server_url,
                ssl=self.ssl_context,
                ping_interval=None,  # 使用应用层心跳
                ping_timeout=None
            )
            
            # 发送认证消息
            self.state = ConnectionState.AUTHENTICATING
            auth_msg = self.protocol.create_message(
                "auth",
                self.config.node_id,
                "cloud-server",
                {
                    "token": self.config.token,
                    "node_type": self.config.node_type,
                    "version": self.config.version,
                    "capabilities": self.config.capabilities
                }
            )
            await self.websocket.send(json.dumps(auth_msg))
            
            # 等待认证响应
            response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=5.0
            )
            
            msg = self.protocol.parse_message(response)
            if not msg or msg.get("msg_type") != "auth_response":
                logger.error("认证响应无效")
                await self.websocket.close()
                return False
            
            payload = msg.get("payload", {})
            if not payload.get("success"):
                logger.error(f"认证失败: {payload.get('error')}")
                await self.websocket.close()
                return False
            
            self.session_id = payload.get("session_id")
            logger.info(f"认证成功，session_id: {self.session_id}")
            
            # 启动后台任务
            self.state = ConnectionState.CONNECTED
            self.reconnect_mgr.reset()
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            if self.config.auto_report_enabled:
                self._auto_report_task = asyncio.create_task(self._auto_report_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"连接失败: {e}")
            self.state = ConnectionState.DISCONNECTED
            return False
    
    async def _reconnect(self):
        """重连逻辑"""
        if not self.config.reconnect_enabled:
            return False
        
        self.state = ConnectionState.RECONNECTING
        
        try:
            delay = self.reconnect_mgr.get_next_delay()
            logger.info(f"{delay:.1f}秒后重连 (尝试 {self.reconnect_mgr.current_attempt})...")
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=delay
            )
            return False  # 收到停止信号
        except asyncio.TimeoutError:
            pass
        
        return await self.connect()
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.state == ConnectionState.CONNECTED and not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.config.heartbeat_interval
                )
                break  # 收到停止信号
            except asyncio.TimeoutError:
                pass
            
            if self.state != ConnectionState.CONNECTED:
                break
            
            # 发送心跳
            self._heartbeat_sequence += 1
            heartbeat_msg = self.protocol.create_message(
                "heartbeat",
                self.config.node_id,
                "cloud-server",
                {
                    "sequence": self._heartbeat_sequence,
                    "status": "alive"
                }
            )
            
            try:
                await self.websocket.send(json.dumps(heartbeat_msg))
                logger.debug(f"发送心跳 #{self._heartbeat_sequence}")
            except Exception as e:
                logger.warning(f"发送心跳失败: {e}")
                break
    
    async def _auto_report_loop(self):
        """自动上报循环"""
        while self.state == ConnectionState.CONNECTED and not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.config.auto_report_interval
                )
                break
            except asyncio.TimeoutError:
                pass
            
            if self.state != ConnectionState.CONNECTED:
                break
            
            try:
                # 获取状态并上报
                status = await self.auto_handler._handle_get_status({})
                await self.send_event("status_report", status)
            except Exception as e:
                logger.warning(f"自动上报失败: {e}")
    
    async def _handle_message(self, message: dict):
        """处理接收到的消息"""
        msg_type = message.get("msg_type")
        
        if msg_type == "heartbeat_ack":
            # 心跳确认
            payload = message.get("payload", {})
            logger.debug(f"收到心跳确认 #{payload.get('sequence')}")
            
        elif msg_type == "request":
            # 处理请求
            await self._handle_request(message)
            
        elif msg_type == "response":
            # 处理响应
            await self._handle_response(message)
            
        elif msg_type == "event":
            # 处理服务器事件
            logger.info(f"收到服务器事件: {message}")
            
        elif msg_type == "error":
            # 处理错误
            payload = message.get("payload", {})
            logger.error(f"收到错误: {payload.get('error_code')} - {payload.get('error_message')}")
    
    async def _handle_request(self, message: dict):
        """处理请求消息（自动响应）"""
        if not self.config.auto_response_enabled:
            return
        
        payload = message.get("payload", {})
        action = payload.get("action", "")
        request_id = payload.get("request_id", "")
        
        logger.info(f"自动响应请求: {action}")
        
        try:
            result = await self.auto_handler.handle(action, payload.get("params", {}))
            success = "error" not in result
            error_code = None if success else "ACTION_FAILED"
            error_message = result.pop("error", None) if not success else None
        except Exception as e:
            result = {}
            success = False
            error_code = "INTERNAL_ERROR"
            error_message = str(e)
        
        # 发送响应
        response = self.protocol.create_message(
            "response",
            self.config.node_id,
            "cloud-server",
            {
                "request_id": request_id,
                "success": success,
                "data": result,
                "error_code": error_code,
                "error_message": error_message
            }
        )
        await self.send_message(response)
    
    async def _handle_response(self, message: dict):
        """处理响应消息"""
        payload = message.get("payload", {})
        request_id = payload.get("request_id", "")
        
        # 唤醒等待的future
        if request_id in self._pending_responses:
            future = self._pending_responses.pop(request_id)
            if not future.done():
                future.set_result(payload)
    
    async def send_message(self, message: dict) -> bool:
        """发送消息"""
        if self.state != ConnectionState.CONNECTED:
            logger.warning("未连接，无法发送消息")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False
    
    async def send_request(self, action: str, params: dict = None, timeout: float = 30.0) -> dict:
        """发送请求并等待响应"""
        request_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()
        self._pending_responses[request_id] = future
        
        request_msg = self.protocol.create_message(
            "request",
            self.config.node_id,
            "cloud-server",
            {
                "action": action,
                "params": params or {},
                "request_id": request_id
            }
        )
        
        if not await self.send_message(request_msg):
            del self._pending_responses[request_id]
            return {"success": False, "error": "Failed to send request"}
        
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            del self._pending_responses[request_id]
            return {"success": False, "error": "Request timeout"}
    
    async def send_event(self, event_type: str, event_data: dict):
        """发送事件"""
        event_msg = self.protocol.create_message(
            "event",
            self.config.node_id,
            "cloud-server",
            {
                "event_type": event_type,
                "event_data": event_data
            }
        )
        await self.send_message(event_msg)
    
    async def run(self):
        """主运行循环"""
        while not self._stop_event.is_set():
            # 尝试连接
            if await self.connect():
                # 连接成功，进入消息接收循环
                try:
                    async for message in self.websocket:
                        msg = self.protocol.parse_message(message)
                        if msg:
                            await self._handle_message(msg)
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("连接关闭")
                except Exception as e:
                    logger.error(f"消息处理异常: {e}")
                finally:
                    self.state = ConnectionState.DISCONNECTED
                    if self._heartbeat_task:
                        self._heartbeat_task.cancel()
                    if self._auto_report_task:
                        self._auto_report_task.cancel()
            
            # 尝试重连
            if self._stop_event.is_set():
                break
            
            if not await self._reconnect():
                break
        
        logger.info("客户端停止")
    
    def stop(self):
        """停止客户端"""
        logger.info("停止客户端...")
        self._stop_event.set()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WebSocket Client')
    parser.add_argument('--url', default='ws://localhost:8765', help='服务器URL')
    parser.add_argument('--node-id', default='local-node-01', help='节点ID')
    parser.add_argument('--token', default='demo-token-12345', help='认证Token')
    parser.add_argument('--no-reconnect', action='store_true', help='禁用自动重连')
    parser.add_argument('--auto-report', action='store_true', help='启用自动上报')
    
    args = parser.parse_args()
    
    config = ClientConfig(
        server_url=args.url,
        node_id=args.node_id,
        token=args.token,
        reconnect_enabled=not args.no_reconnect,
        auto_report_enabled=args.auto_report
    )
    
    client = WebSocketClient(config)
    
    # 信号处理
    loop = asyncio.get_event_loop()
    for sig in ('SIGINT', 'SIGTERM'):
        try:
            loop.add_signal_handler(
                getattr(__import__('signal'), sig),
                client.stop
            )
        except NotImplementedError:
            pass
    
    # 启动客户端
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
