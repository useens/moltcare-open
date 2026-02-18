# Evolution Core - Event Bus and State Management

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class Event:
    """系统事件"""
    type: str
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

class EventBus:
    """简单事件总线（发布-订阅）"""
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: Event):
        """发布事件"""
        handlers = self._subscribers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"[EventBus] Handler error: {e}")

class StateManager:
    """系统状态管理"""
    def __init__(self, state_file: str = "/root/.openclaw/workspace/evolution/state.json"):
        self.state_file = Path(state_file)
        self.state = self._load_state()
        self.event_bus = EventBus()

    def _load_state(self) -> Dict:
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "version": "2.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "evolution_enabled": True,
            "current_model": "nvidia-build/stepfun-ai/step-3.5-flash",
            "stats": {
                "total_evolutions": 0,
                "successful_evolutions": 0,
                "failed_evolutions": 0,
                "last_evolution": None
            },
            "config": {
                "confidence_threshold": 0.8,
                "sandbox_enabled": True,
                "auto_rollback": True,
                "max_concurrent": 1
            }
        }

    def save(self):
        """保存状态"""
        self.state["last_updated"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get(self, key: str, default=None):
        """获取状态值"""
        return self.state.get(key, default)

    def set(self, key: str, value: Any):
        """设置状态值"""
        self.state[key] = value
        self.save()
        self.event_bus.publish(Event(
            type="state.changed",
            source="StateManager",
            timestamp=datetime.now(),
            data={"key": key, "value": value}
        ))

# 全局实例
state = StateManager()
event_bus = state.event_bus
