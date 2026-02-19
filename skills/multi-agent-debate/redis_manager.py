"""
Multi-Agent Debate - Redis 实时同步模块
Phase 1 实施方案
"""
import redis
import json
import time
import threading
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class AgentUpdate:
    """专家更新消息"""
    round_num: int
    agent_name: str
    status: str  # 'thinking', 'updated', 'complete'
    content: Optional[str] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> 'AgentUpdate':
        return cls(**json.loads(data))


class DebateRedisManager:
    """
    Multi-Agent 辩论 Redis 管理器
    
    核心功能：
    1. 存储每轮讨论内容 (Hash)
    2. 实时推送更新 (Pub/Sub)
    3. 追踪进度 (String)
    4. 超时控制 (TTL)
    """
    
    def __init__(self, host='localhost', port=6380, db=0, password=None):
        self.r = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
        self.pubsub = None
        self._running = False
        
    def test_connection(self) -> bool:
        """测试Redis连接"""
        try:
            return self.r.ping()
        except redis.ConnectionError:
            return False
    
    # ==================== 状态存储 (Hash) ====================
    
    def save_thought(self, debate_id: str, round_num: int, agent_name: str, content: str):
        """保存专家的思考内容"""
        key = f"debate:{debate_id}:round:{round_num}"
        self.r.hset(key, agent_name, content)
        # 设置TTL: 2分钟超时
        self.r.expire(key, 120)
    
    def get_thought(self, debate_id: str, round_num: int, agent_name: str) -> Optional[str]:
        """获取专家的思考内容"""
        key = f"debate:{debate_id}:round:{round_num}"
        return self.r.hget(key, agent_name)
    
    def get_all_thoughts(self, debate_id: str, round_num: int) -> Dict[str, str]:
        """获取该轮所有专家的观点"""
        key = f"debate:{debate_id}:round:{round_num}"
        return self.r.hgetall(key)
    
    # ==================== 实时通知 (Pub/Sub) ====================
    
    def publish_update(self, debate_id: str, update: AgentUpdate):
        """发布实时更新通知"""
        channel = f"debate:{debate_id}:updates"
        self.r.publish(channel, update.to_json())
    
    def subscribe_updates(self, debate_id: str, callback: Callable[[AgentUpdate], None]):
        """订阅实时更新"""
        channel = f"debate:{debate_id}:updates"
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe(channel)
        self._running = True
        
        def listen():
            for message in self.pubsub.listen():
                if not self._running:
                    break
                if message['type'] == 'message':
                    try:
                        update = AgentUpdate.from_json(message['data'])
                        callback(update)
                    except Exception as e:
                        print(f"Error processing update: {e}")
        
        # 在后台线程监听
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()
    
    def unsubscribe(self):
        """取消订阅"""
        self._running = False
        if self.pubsub:
            self.pubsub.unsubscribe()
            self.pubsub.close()
    
    # ==================== 进度追踪 (String) ====================
    
    def set_progress(self, debate_id: str, agent_name: str, status: str):
        """设置专家进度"""
        key = f"debate:{debate_id}:progress:{agent_name}"
        self.r.set(key, status)
        self.r.expire(key, 600)  # 10分钟超时
    
    def get_progress(self, debate_id: str, agent_name: str) -> Optional[str]:
        """获取专家进度"""
        key = f"debate:{debate_id}:progress:{agent_name}"
        return self.r.get(key)
    
    def get_all_progress(self, debate_id: str) -> Dict[str, str]:
        """获取所有专家进度"""
        pattern = f"debate:{debate_id}:progress:*"
        keys = self.r.keys(pattern)
        result = {}
        for key in keys:
            agent = key.split(':')[-1]
            result[agent] = self.r.get(key)
        return result
    
    # ==================== 辩论状态管理 ====================
    
    def set_debate_status(self, debate_id: str, status: str):
        """
        设置辩论整体状态
        status: 'preparing', 'round1', 'round2', 'round3', 'consensus', 'completed'
        """
        key = f"debate:{debate_id}:status"
        self.r.set(key, status)
    
    def get_debate_status(self, debate_id: str) -> Optional[str]:
        """获取辩论整体状态"""
        key = f"debate:{debate_id}:status"
        return self.r.get(key)
    
    # ==================== 元数据存储 ====================
    
    def create_debate(self, debate_id: str, topic: str, agents: List[str]):
        """创建辩论会话"""
        meta = {
            'topic': topic,
            'agents': json.dumps(agents),
            'created_at': datetime.now().isoformat(),
            'current_round': '0'
        }
        key = f"debate:{debate_id}:meta"
        self.r.hset(key, mapping=meta)
        self.set_debate_status(debate_id, 'preparing')
    
    def get_debate_meta(self, debate_id: str) -> Dict:
        """获取辩论元数据"""
        key = f"debate:{debate_id}:meta"
        return self.r.hgetall(key)
    
    # ==================== 统计信息 ====================
    
    def get_stats(self, debate_id: str) -> Dict:
        """获取辩论统计信息"""
        status = self.get_debate_status(debate_id)
        progress = self.get_all_progress(debate_id)
        
        return {
            'status': status,
            'agents_completed': len([v for v in progress.values() if 'complete' in v]),
            'agents_total': len(progress),
            'progress': progress
        }
    
    # ==================== 清理 ====================
    
    def cleanup_debate(self, debate_id: str):
        """清理辩论数据"""
        pattern = f"debate:{debate_id}:*"
        keys = self.r.keys(pattern)
        if keys:
            self.r.delete(*keys)


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 测试连接
    manager = DebateRedisManager(port=6380)
    
    if not manager.test_connection():
        print("❌ Redis连接失败")
        exit(1)
    
    print("✅ Redis连接成功")
    
    # 创建辩论
    debate_id = "test-debate-001"
    manager.create_debate(
        debate_id=debate_id,
        topic="设计高性能Python Web API",
        agents=['harper', 'benjamin', 'lucas']
    )
    
    # 模拟专家更新
    def on_update(update: AgentUpdate):
        print(f"[实时更新] {update.agent_name}: {update.status}")
    
    # 订阅更新
    manager.subscribe_updates(debate_id, on_update)
    
    # 模拟Harper更新
    manager.save_thought(debate_id, 1, 'harper', 'FastAPI性能最优...')
    manager.set_progress(debate_id, 'harper', 'round1:complete')
    manager.publish_update(debate_id, AgentUpdate(
        round_num=1,
        agent_name='harper',
        status='complete',
        content='FastAPI性能最优...'
    ))
    
    time.sleep(1)
    
    # 查看统计
    stats = manager.get_stats(debate_id)
    print(f"\n统计: {stats}")
    
    # 获取所有观点
    thoughts = manager.get_all_thoughts(debate_id, 1)
    print(f"\nRound 1 观点: {thoughts}")
    
    # 清理
    time.sleep(2)
    manager.unsubscribe()
    manager.cleanup_debate(debate_id)
    print("\n✅ 测试完成")
