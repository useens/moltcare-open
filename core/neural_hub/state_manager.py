"""
神经中枢 2.0 - 状态管理器
实时跟踪所有nanobot的状态
"""
import asyncio
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class BotState:
    """Bot状态"""
    bot_id: str
    name: str
    role: str
    state: str = 'offline'  # offline, idle, busy, paused, error
    capabilities: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    last_heartbeat: float = 0.0
    success_rate: float = 1.0
    total_tasks: int = 0
    failed_tasks: int = 0
    
    @property
    def is_online(self) -> bool:
        """是否在线（30秒内有心跳）"""
        return time.time() - self.last_heartbeat < 30
    
    @property
    def is_available(self) -> bool:
        """是否可用（在线且空闲）"""
        return self.is_online and self.state == 'idle'
    
    @property
    def load_score(self) -> float:
        """负载评分（越低越好）"""
        if not self.is_online:
            return float('inf')
        if self.state == 'busy':
            return 100.0
        if self.state == 'paused':
            return 50.0
        return self.total_tasks * 0.1  # 历史任务数作为参考

class StateManager:
    """状态管理中心"""
    
    def __init__(self, database=None):
        self.bots: Dict[str, BotState] = {}
        self.database = database
        self._callbacks: List[Callable] = []
        self._running = False
        self._monitor_task = None
        
    def register_bot(self, bot_id: str, name: str, role: str, 
                     capabilities: List[str]):
        """注册bot"""
        self.bots[bot_id] = BotState(
            bot_id=bot_id,
            name=name,
            role=role,
            capabilities=capabilities,
            state='idle',
            last_heartbeat=time.time()
        )
        
        # 持久化
        if self.database:
            self.database.register_bot(bot_id, name, role, capabilities)
        
        self._notify_change('bot_registered', bot_id)
        print(f"[State] Bot注册: {bot_id} ({name})")
    
    def update_state(self, bot_id: str, state: str, current_task: str = None):
        """更新状态"""
        if bot_id not in self.bots:
            return False
        
        old_state = self.bots[bot_id].state
        self.bots[bot_id].state = state
        self.bots[bot_id].current_task = current_task
        
        # 持久化
        if self.database:
            self.database.update_bot_status(bot_id, state, current_task)
        
        self._notify_change('state_change', bot_id, {
            'old': old_state,
            'new': state
        })
        return True
    
    def heartbeat(self, bot_id: str):
        """更新心跳"""
        if bot_id not in self.bots:
            return False
        
        self.bots[bot_id].last_heartbeat = time.time()
        
        # 如果离线，恢复为idle
        if self.bots[bot_id].state == 'offline':
            self.bots[bot_id].state = 'idle'
            self._notify_change('bot_online', bot_id)
        
        # 持久化
        if self.database:
            self.database.heartbeat(bot_id)
        
        return True
    
    def get_bot(self, bot_id: str) -> Optional[BotState]:
        """获取bot状态"""
        return self.bots.get(bot_id)
    
    def get_all_bots(self) -> List[BotState]:
        """获取所有bot"""
        return list(self.bots.values())
    
    def get_online_bots(self) -> List[BotState]:
        """获取在线bot"""
        return [b for b in self.bots.values() if b.is_online]
    
    def get_available_bots(self) -> List[BotState]:
        """获取可用bot（在线且空闲）"""
        return [b for b in self.bots.values() if b.is_available]
    
    def get_bots_by_capability(self, capability: str) -> List[BotState]:
        """按能力筛选bot"""
        return [
            b for b in self.bots.values()
            if b.is_online and capability in b.capabilities
        ]
    
    def get_best_bot_for_task(self, required_capabilities: List[str]) -> Optional[BotState]:
        """选择最适合任务的bot"""
        candidates = []
        
        for bot in self.bots.values():
            if not bot.is_available:
                continue
            
            # 检查能力匹配
            if all(cap in bot.capabilities for cap in required_capabilities):
                candidates.append(bot)
        
        if not candidates:
            return None
        
        # 按负载评分排序
        candidates.sort(key=lambda b: b.load_score)
        return candidates[0]
    
    def update_task_stats(self, bot_id: str, success: bool):
        """更新任务统计"""
        if bot_id not in self.bots:
            return
        
        bot = self.bots[bot_id]
        bot.total_tasks += 1
        
        if not success:
            bot.failed_tasks += 1
        
        # 更新成功率
        if bot.total_tasks > 0:
            bot.success_rate = 1.0 - (bot.failed_tasks / bot.total_tasks)
    
    def on_state_change(self, callback: Callable):
        """注册状态变更回调"""
        self._callbacks.append(callback)
    
    def _notify_change(self, event: str, bot_id: str, data: dict = None):
        """通知状态变更"""
        for callback in self._callbacks:
            try:
                callback(event, bot_id, data)
            except Exception as e:
                print(f"[State] 回调错误: {e}")
    
    async def start_monitor(self):
        """启动状态监控"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        print("[State] 状态监控已启动")
    
    async def stop_monitor(self):
        """停止状态监控"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
        print("[State] 状态监控已停止")
    
    async def _monitor_loop(self):
        """监控循环 - 检测离线bot"""
        while self._running:
            try:
                current_time = time.time()
                
                for bot_id, bot in self.bots.items():
                    # 检测离线（超过90秒无心跳）
                    if (bot.state != 'offline' and 
                        current_time - bot.last_heartbeat > 90):
                        print(f"[State] Bot离线: {bot_id}")
                        bot.state = 'offline'
                        bot.current_task = None
                        self._notify_change('bot_offline', bot_id)
                
                await asyncio.sleep(10)  # 每10秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[State] 监控错误: {e}")
                await asyncio.sleep(10)
    
    def get_summary(self) -> dict:
        """获取状态摘要"""
        total = len(self.bots)
        online = len(self.get_online_bots())
        available = len(self.get_available_bots())
        busy = len([b for b in self.bots.values() if b.state == 'busy'])
        offline = total - online
        
        return {
            'total_bots': total,
            'online': online,
            'available': available,
            'busy': busy,
            'offline': offline,
            'timestamp': datetime.now().isoformat()
        }
