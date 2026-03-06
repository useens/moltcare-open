#!/usr/bin/env python3
"""
Nanobot V3 - 神经中枢 2.0 客户端
支持 Redis Pub/Sub 和实时任务执行
"""
import os
import sys
import json
import asyncio
import signal
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

# 可选依赖
try:
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        import aioredis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False

@dataclass
class BotConfig:
    """Bot配置"""
    bot_id: str
    name: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    redis_url: str = "redis://127.0.0.1:6380/0"
    heartbeat_interval: int = 30

try:
    from core.neural_hub.redis_client import RedisClient
except ImportError:
    # 如果导入失败，使用内嵌的简单实现
    class RedisClient:
        def __init__(self, *args, **kwargs):
            self._connected = False
        async def connect(self): pass
        async def disconnect(self): pass

class NanobotV3:
    """
    Nanobot V3 客户端
    
    新特性:
    - Redis Pub/Sub 实时通信
    - 任务执行框架
    - 心跳自动上报
    - 能力动态注册
    """
    
    # Redis频道
    CHANNELS = {
        'commands': 'neuralhub:commands',
        'responses': 'neuralhub:responses',
        'events': 'neuralhub:events',
        'heartbeat': 'neuralhub:heartbeat',
        'control': 'neuralhub:control',
    }
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.redis: Optional[RedisClient] = None
        self._connected = False
        self._running = False
        self._current_task: Optional[str] = None
        self._state = 'idle'  # idle, busy, paused, error
        self._shutdown_event = asyncio.Event()
        
        # 任务处理器注册表
        self._handlers: Dict[str, Callable] = {}
        
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self._handlers[task_type] = handler
        print(f"[{self.config.bot_id}] 注册处理器: {task_type}")
    
    # ========== 核心方法 ==========
    
    async def connect(self):
        """连接到神经中枢"""
        if not REDIS_AVAILABLE:
            print(f"[{self.config.bot_id}] ⚠️ Redis库未安装，以降级模式运行")
            self._connected = False
            return
        
        try:
            # 兼容两种导入方式
            if hasattr(aioredis, 'from_url'):
                self.redis = await aioredis.from_url(
                    self.config.redis_url,
                    decode_responses=True
                )
            else:
                self.redis = aioredis.Redis.from_url(
                    self.config.redis_url,
                    decode_responses=True
                )
            self._connected = True
            print(f"[{self.config.bot_id}] ✅ 已连接到神经中枢")
        except Exception as e:
            print(f"[{self.config.bot_id}] ❌ 连接失败: {e}")
            self._connected = False
    
    async def disconnect(self):
        """断开连接"""
        if self.redis:
            await self.redis.close()
        self._connected = False
        print(f"[{self.config.bot_id}] 已断开连接")
    
    async def start(self):
        """启动Bot"""
        print(f"\n🤖 {self.config.name} ({self.config.bot_id}) 启动中...")
        print(f"   角色: {self.config.role}")
        print(f"   能力: {', '.join(self.config.capabilities)}")
        
        # 连接Redis
        await self.connect()
        
        if self._connected:
            # 注册到神经中枢
            await self._register()
            
            # 订阅频道
            await self._subscribe_channels()
            
            # 启动心跳
            asyncio.create_task(self._heartbeat_loop())
        
        self._running = True
        print(f"[{self.config.bot_id}] ✅ 已启动，等待指令...\n")
        
        # 等待关闭
        await self._shutdown_event.wait()
    
    async def stop(self):
        """停止Bot"""
        print(f"\n[{self.config.bot_id}] 关闭中...")
        self._running = False
        self._shutdown_event.set()
        await self.disconnect()
    
    # ========== 通信方法 ==========
    
    async def _register(self):
        """向神经中枢注册"""
        await self._send_message('responses', {
            'type': 'register',
            'data': {
                'bot_id': self.config.bot_id,
                'name': self.config.name,
                'role': self.config.role,
                'capabilities': self.config.capabilities
            }
        })
    
    async def _subscribe_channels(self):
        """订阅频道"""
        pubsub = self.redis.pubsub()
        
        # 订阅命令频道（广播+定向）
        await pubsub.subscribe(self.CHANNELS['commands'])
        await pubsub.subscribe(f"{self.CHANNELS['control']}:{self.config.bot_id}")
        
        # 启动消息处理
        asyncio.create_task(self._message_loop(pubsub))
    
    async def _message_loop(self, pubsub):
        """消息处理循环"""
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    print(f"[{self.config.bot_id}] 消息处理错误: {e}")
    
    async def _handle_message(self, message: dict):
        """处理收到的消息"""
        routing = message.get('routing', {})
        payload = message.get('payload', {})
        
        to = routing.get('to', '')
        msg_type = payload.get('type')
        action = payload.get('action')
        data = payload.get('data', {})
        
        # 检查是否发给自己
        if to not in ['broadcast', self.config.bot_id]:
            return
        
        print(f"[{self.config.bot_id}] 收到指令: {action}")
        
        # 处理不同类型的消息
        if msg_type == 'command':
            await self._handle_command(action, data)
        elif msg_type == 'control':
            await self._handle_control(action, data)
    
    async def _handle_command(self, action: str, data: dict):
        """处理命令"""
        if action == 'ping':
            await self._send_response('pong', {'timestamp': datetime.now().isoformat()})
        
        elif action == 'get_status':
            await self._send_response('status_report', {
                'state': self._state,
                'current_task': self._current_task,
                'capabilities': self.config.capabilities
            })
        
        elif action == 'assign_task':
            task_id = data.get('task_id')
            task_type = data.get('type')
            task_data = data.get('payload', {})
            
            if self._state == 'busy':
                await self._send_response('task_rejected', {
                    'task_id': task_id,
                    'reason': 'busy'
                })
            else:
                asyncio.create_task(self._execute_task(task_id, task_type, task_data))
        
        else:
            print(f"[{self.config.bot_id}] 未知命令: {action}")
    
    async def _handle_control(self, action: str, data: dict):
        """处理控制指令 (高优先级)"""
        if action == 'pause':
            self._state = 'paused'
            print(f"[{self.config.bot_id}] 已暂停")
        
        elif action == 'resume':
            self._state = 'idle'
            print(f"[{self.config.bot_id}] 已恢复")
        
        elif action == 'shutdown':
            await self.stop()
    
    async def _execute_task(self, task_id: str, task_type: str, data: dict):
        """执行任务"""
        self._state = 'busy'
        self._current_task = task_id
        
        print(f"[{self.config.bot_id}] 开始执行任务: {task_id} ({task_type})")
        
        try:
            # 查找处理器
            handler = self._handlers.get(task_type)
            
            if handler:
                # 执行处理器
                result = await handler(data)
                
                # 报告完成
                await self._send_response('task_complete', {
                    'task_id': task_id,
                    'result': result
                })
            else:
                # 没有处理器，模拟执行
                await asyncio.sleep(1)
                
                await self._send_response('task_complete', {
                    'task_id': task_id,
                    'result': {'status': 'completed', 'handler': 'default'}
                })
        
        except Exception as e:
            print(f"[{self.config.bot_id}] 任务执行错误: {e}")
            await self._send_response('task_failed', {
                'task_id': task_id,
                'error': str(e)
            })
        
        finally:
            self._state = 'idle'
            self._current_task = None
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                await self._send_message('heartbeat', {
                    'state': self._state,
                    'current_task': self._current_task,
                    'timestamp': datetime.now().isoformat()
                })
                await asyncio.sleep(self.config.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[{self.config.bot_id}] 心跳错误: {e}")
                await asyncio.sleep(5)
    
    async def _send_message(self, channel: str, data: dict):
        """发送消息"""
        if not self._connected:
            return
        
        message = {
            'header': {
                'msg_id': f"{self.config.bot_id}-{datetime.now().timestamp()}",
                'timestamp': datetime.now().timestamp()
            },
            'routing': {
                'from': self.config.bot_id,
                'to': 'openclaw'
            },
            'payload': data
        }
        
        await self.redis.publish(self.CHANNELS[channel], json.dumps(message))
    
    async def _send_response(self, msg_type: str, data: dict):
        """发送响应"""
        await self._send_message('responses', {
            'type': msg_type,
            'data': data
        })


# ========== 启动入口 ==========

def create_nanobot(bot_id: str, name: str, role: str, 
                   capabilities: List[str]) -> NanobotV3:
    """创建Nanobot实例"""
    config = BotConfig(
        bot_id=bot_id,
        name=name,
        role=role,
        capabilities=capabilities
    )
    return NanobotV3(config)


async def main():
    """测试入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nanobot V3')
    parser.add_argument('--id', default='nanobot-test', help='Bot ID')
    parser.add_argument('--name', default='测试Bot', help='Bot名称')
    parser.add_argument('--role', default='tester', help='Bot角色')
    args = parser.parse_args()
    
    # 创建Bot
    bot = create_nanobot(
        bot_id=args.id,
        name=args.name,
        role=args.role,
        capabilities=['test', 'echo']
    )
    
    # 注册处理器
    async def echo_handler(data):
        return {'echo': data, 'processed_by': args.id}
    
    bot.register_handler('echo', echo_handler)
    
    # 信号处理
    def signal_handler():
        asyncio.create_task(bot.stop())
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await bot.start()
    except Exception as e:
        print(f"启动错误: {e}")
        await bot.stop()


if __name__ == '__main__':
    asyncio.run(main())
