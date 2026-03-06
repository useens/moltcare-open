"""
神经中枢 2.0 - Redis客户端
提供Pub/Sub消息总线功能 - 支持降级模式
"""
import json
import asyncio
from typing import Callable, Optional
from datetime import datetime

try:
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        import aioredis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False
        aioredis = None


class RedisClient:
    """Redis消息总线客户端 - 支持降级模式"""
    
    CHANNELS = {
        'commands': 'neuralhub:commands',
        'responses': 'neuralhub:responses',
        'events': 'neuralhub:events',
        'heartbeat': 'neuralhub:heartbeat',
        'control': 'neuralhub:control',
        'status': 'neuralhub:status',
    }
    
    def __init__(self, redis_url: str = "redis://localhost:6380"):
        self.redis_url = redis_url
        self.redis = None
        self.pubsub = None
        self.subscribers = {}
        self._connected = False
        self._degraded_mode = False
        
    async def connect(self):
        """连接Redis - 失败时进入降级模式"""
        if not REDIS_AVAILABLE:
            print("[Redis] ⚠️ redis库未安装，进入降级模式")
            self._degraded_mode = True
            return
        
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True
            )
            await self.redis.ping()
            self._connected = True
            print(f"[Redis] ✅ 已连接到 {self.redis_url}")
        except Exception as e:
            print(f"[Redis] ⚠️ 连接失败: {e}")
            print("[Redis] 进入降级模式 (仅使用本地功能)")
            self._degraded_mode = True
            self.redis = None
    
    async def disconnect(self):
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        self._connected = False
    
    async def publish(self, channel: str, message: dict):
        if self._degraded_mode:
            return True
        if not self._connected:
            return False
        message['timestamp'] = datetime.now().timestamp()
        await self.redis.publish(channel, json.dumps(message))
        return True
    
    async def subscribe(self, channel: str, callback: Callable):
        if self._degraded_mode:
            return
        if not self._connected:
            return
        await self.pubsub.subscribe(channel)
        self.subscribers[channel] = callback
        asyncio.create_task(self._listen(channel, callback))
    
    async def _listen(self, channel: str, callback: Callable):
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    await callback(data)
                except Exception as e:
                    print(f"[Redis] 处理错误: {e}")
    
    async def send_command(self, target: str, action: str, data: dict = None):
        if self._degraded_mode:
            return True
        message = {
            'header': {'msg_id': f"cmd-{datetime.now().timestamp()}", 'priority': 3},
            'routing': {'from': 'openclaw', 'to': target},
            'payload': {'type': 'command', 'action': action, 'data': data or {}}
        }
        return await self.publish(self.CHANNELS['commands'], message)
    
    async def broadcast(self, action: str, data: dict = None):
        if self._degraded_mode:
            return True
        return await self.send_command('broadcast', action, data)
    
    async def ping_bot(self, bot_id: str):
        if self._degraded_mode:
            return True
        return await self.send_command(bot_id, 'ping')
    
    async def assign_task(self, bot_id: str, task: dict):
        if self._degraded_mode:
            return True
        return await self.send_command(bot_id, 'assign_task', task)
    
    async def request_status(self, bot_id: str = 'broadcast'):
        if self._degraded_mode:
            return True
        return await self.send_command(bot_id, 'get_status')
    
    @property
    def is_degraded(self) -> bool:
        return self._degraded_mode
