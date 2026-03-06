"""
神经中枢 2.0 - 主服务
整合所有组件，提供统一API
"""
import asyncio
import json
import signal
from typing import Optional
from .state_manager import StateManager
from .scheduler import SmartScheduler, TaskPriority
from .database import TaskDatabase
from .redis_client import RedisClient

class NeuralHub:
    """神经中枢主服务"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.db = TaskDatabase()
        self.state = StateManager(self.db)
        self.redis = RedisClient(redis_url)
        self.scheduler = SmartScheduler(self.state, self.db, self.redis)
        
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # 注册默认bot
        self._register_default_bots()
    
    def _register_default_bots(self):
        """注册10个默认nanobot"""
        bots_config = [
            ("nanobot-1", "研究员", "researcher", ["research", "data_analysis", "search"]),
            ("nanobot-2", "架构师", "architect", ["design", "architecture", "planning"]),
            ("nanobot-3", "工程师", "engineer", ["coding", "debugging", "testing"]),
            ("nanobot-4", "安全专家", "security", ["security", "audit", "pentest"]),
            ("nanobot-5", "分析师", "analyst", ["analysis", "reporting", "metrics"]),
            ("nanobot-6", "决策分析师", "decision", ["decision", "evaluation", "strategy"]),
            ("nanobot-7", "代码审查员", "reviewer", ["code_review", "quality", "standards"]),
            ("nanobot-8", "运维专家", "ops", ["ops", "monitoring", "deployment"]),
            ("nanobot-9", "战略规划师", "strategist", ["strategy", "planning", "roadmap"]),
            ("nanobot-10", "协调者", "coordinator", ["coordination", "communication", "sync"]),
        ]
        
        for bot_id, name, role, capabilities in bots_config:
            self.state.register_bot(bot_id, name, role, capabilities)
    
    async def start(self):
        """启动服务"""
        print("🧠 神经中枢 2.0 启动中...")
        
        # 连接Redis
        try:
            await self.redis.connect()
        except Exception as e:
            print(f"⚠️ Redis连接失败: {e}")
            print("   继续以降级模式运行...")
        
        # 启动状态监控
        await self.state.start_monitor()
        
        # 启动调度器
        await self.scheduler.start()
        
        # 订阅响应频道
        if self.redis._connected:
            await self.redis.subscribe(
                self.redis.CHANNELS['responses'],
                self._handle_response
            )
            await self.redis.subscribe(
                self.redis.CHANNELS['heartbeat'],
                self._handle_heartbeat
            )
        
        self._running = True
        print("✅ 神经中枢 2.0 已启动")
        print(f"   已注册 {len(self.state.bots)} 个nanobot")
        
        # 等待关闭信号
        await self._shutdown_event.wait()
    
    async def stop(self):
        """停止服务"""
        print("\n🛑 神经中枢 2.0 关闭中...")
        
        self._running = False
        self._shutdown_event.set()
        
        # 停止调度器
        await self.scheduler.stop()
        
        # 停止状态监控
        await self.state.stop_monitor()
        
        # 断开Redis
        await self.redis.disconnect()
        
        print("✅ 神经中枢 2.0 已关闭")
    
    # ========== 任务管理 API ==========
    
    async def submit_task(self, task_type: str, payload: dict = None,
                          priority: int = 3,
                          required_capabilities: list = None) -> str:
        """提交任务"""
        priority_enum = TaskPriority(min(priority, 4))
        task_id = self.scheduler.submit_task(
            task_type, payload, priority_enum, required_capabilities
        )
        
        # 广播任务创建事件
        if self.redis._connected:
            await self.redis.publish(
                self.redis.CHANNELS['events'],
                {
                    'type': 'task_created',
                    'task_id': task_id,
                    'task_type': task_type
                }
            )
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """获取任务状态"""
        task = self.scheduler.get_task_status(task_id)
        if task:
            return {
                'id': task.id,
                'type': task.type,
                'status': task.status.value,
                'priority': task.priority.name,
                'assigned_to': task.assigned_to,
                'created_at': task.created_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'retry_count': task.retry_count,
                'error': task.error
            }
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        return self.scheduler.cancel_task(task_id)
    
    # ========== Bot管理 API ==========
    
    async def get_bot_status(self, bot_id: str) -> Optional[dict]:
        """获取bot状态"""
        bot = self.state.get_bot(bot_id)
        if bot:
            return {
                'bot_id': bot.bot_id,
                'name': bot.name,
                'role': bot.role,
                'state': bot.state,
                'is_online': bot.is_online,
                'is_available': bot.is_available,
                'capabilities': bot.capabilities,
                'current_task': bot.current_task,
                'success_rate': bot.success_rate,
                'total_tasks': bot.total_tasks
            }
        return None
    
    async def list_bots(self) -> list:
        """列出所有bot"""
        return [
            {
                'bot_id': b.bot_id,
                'name': b.name,
                'state': b.state,
                'is_online': b.is_online
            }
            for b in self.state.get_all_bots()
        ]
    
    async def ping_bot(self, bot_id: str):
        """Ping指定bot"""
        if self.redis._connected:
            await self.redis.ping_bot(bot_id)
    
    async def broadcast(self, message: str, priority: int = 3):
        """广播消息"""
        if self.redis._connected:
            await self.redis.broadcast('message', {'content': message})
    
    # ========== 系统 API ==========
    
    async def get_stats(self) -> dict:
        """获取系统统计"""
        return {
            'bots': self.state.get_summary(),
            'tasks': self.scheduler.get_stats(),
            'database': self.db.get_stats() if self.db else {}
        }
    
    # ========== 消息处理 ==========
    
    async def _handle_response(self, message: dict):
        """处理bot响应"""
        payload = message.get('payload', {})
        msg_type = payload.get('type')
        
        if msg_type == 'task_complete':
            task_id = payload.get('data', {}).get('task_id')
            result = payload.get('data', {}).get('result')
            if task_id:
                self.scheduler.complete_task(task_id, result)
        
        elif msg_type == 'task_failed':
            task_id = payload.get('data', {}).get('task_id')
            error = payload.get('data', {}).get('error')
            if task_id:
                self.scheduler.fail_task(task_id, error)
        
        elif msg_type == 'status_report':
            bot_id = message.get('routing', {}).get('from')
            state = payload.get('data', {}).get('state')
            current_task = payload.get('data', {}).get('current_task')
            if bot_id:
                self.state.update_state(bot_id, state, current_task)
    
    async def _handle_heartbeat(self, message: dict):
        """处理心跳"""
        bot_id = message.get('routing', {}).get('from')
        if bot_id:
            self.state.heartbeat(bot_id)

# 启动入口
async def main():
    hub = NeuralHub()
    
    # 信号处理
    def signal_handler():
        asyncio.create_task(hub.stop())
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await hub.start()
    except Exception as e:
        print(f"启动错误: {e}")
        await hub.stop()

if __name__ == '__main__':
    asyncio.run(main())
