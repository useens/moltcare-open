"""
MultiAgentDebate - 可复用的多智能体辩论系统

核心类：MultiAgentDebate
提供简洁的API接口，支持自定义专家、主题和回调
"""
import redis
import json
import time
import threading
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class DebateStatus(Enum):
    """辩论状态枚举"""
    PREPARING = "preparing"
    ROUND_1 = "round1"
    ROUND_2 = "round2" 
    ROUND_3 = "round3"
    CONSENSUS = "consensus"
    COMPLETED = "completed"

class AgentRole(Enum):
    """专家角色枚举"""
    RESEARCHER = "researcher"    # Harper - 研究/数据
    ARCHITECT = "architect"      # Benjamin - 架构/安全
    IMPLEMENTER = "implementer"  # Lucas - 实现/工程
    LEADER = "leader"            # Grok - 队长/整合
    CUSTOM = "custom"            # 自定义角色

@dataclass
class Agent:
    """专家定义"""
    name: str
    role: AgentRole
    description: str
    system_prompt: str
    model: str = "kimi-coding/k2p5"
    
    def __post_init__(self):
        if self.system_prompt is None:
            self.system_prompt = self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """获取默认角色提示词"""
        prompts = {
            AgentRole.RESEARCHER: "你是研究专家，负责技术调研、数据支持和最佳实践分析。",
            AgentRole.ARCHITECT: "你是架构专家，负责整体设计、安全考量和长期可维护性。",
            AgentRole.IMPLEMENTER: "你是实现专家，负责代码可行性、工期评估和潜在坑点。",
            AgentRole.LEADER: "你是队长，负责整合各方意见，做出最终决策。",
            AgentRole.CUSTOM: "你是领域专家，提供专业分析和建议。"
        }
        return prompts.get(self.role, prompts[AgentRole.CUSTOM])

@dataclass
class DebateConfig:
    """辩论配置"""
    topic: str
    agents: List[Agent] = field(default_factory=list)
    rounds: int = 3
    timeout_per_round: int = 120  # 秒
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_password: Optional[str] = None
    enable_notifications: bool = True
    notification_callback: Optional[Callable] = None

class MultiAgentDebate:
    """
    Multi-Agent 辩论系统主类
    
    使用示例:
    ```python
    from multi_agent_debate import MultiAgentDebate, Agent, AgentRole
    
    # 定义专家
    agents = [
        Agent("Harper", AgentRole.RESEARCHER, "技术调研专家"),
        Agent("Benjamin", AgentRole.ARCHITECT, "架构设计专家"),
        Agent("Lucas", AgentRole.IMPLEMENTER, "代码实现专家")
    ]
    
    # 创建辩论
    debate = MultiAgentDebate(
        topic="设计高性能Web API",
        agents=agents
    )
    
    # 运行辩论
    result = debate.start()
    
    # 获取结果
    print(result['consensus'])
    ```
    """
    
    def __init__(self, topic: str, agents: Optional[List[Agent]] = None, 
                 config: Optional[DebateConfig] = None, **kwargs):
        """
        初始化辩论
        
        Args:
            topic: 辩论主题
            agents: 专家列表（可选，使用默认专家）
            config: 完整配置（可选）
            **kwargs: 其他配置参数
        """
        self.topic = topic
        self.debate_id = kwargs.get('debate_id', f"debate-{int(time.time())}")
        
        # 配置
        if config:
            self.config = config
        else:
            self.config = DebateConfig(
                topic=topic,
                agents=agents or self._default_agents(),
                **{k: v for k, v in kwargs.items() if hasattr(DebateConfig, k)}
            )
        
        # Redis连接
        self.redis = redis.Redis(
            host=self.config.redis_host,
            port=self.config.redis_port,
            password=self.config.redis_password,
            decode_responses=True
        )
        
        # 状态
        self.status = DebateStatus.PREPARING
        self.start_time = None
        self.end_time = None
        self.messages = []
        
        # 回调
        self.on_round_complete: Optional[Callable] = None
        self.on_consensus: Optional[Callable] = None
        self.on_update: Optional[Callable] = None
    
    def _default_agents(self) -> List[Agent]:
        """获取默认专家配置"""
        return [
            Agent("Harper", AgentRole.RESEARCHER, "技术调研专家", None),
            Agent("Benjamin", AgentRole.ARCHITECT, "架构设计专家", None),
            Agent("Lucas", AgentRole.IMPLEMENTER, "代码实现专家", None)
        ]
    
    def register_callback(self, event: str, callback: Callable):
        """
        注册事件回调
        
        Args:
            event: 'round_complete', 'consensus', 'update'
            callback: 回调函数
        """
        if event == 'round_complete':
            self.on_round_complete = callback
        elif event == 'consensus':
            self.on_consensus = callback
        elif event == 'update':
            self.on_update = callback
    
    def start(self) -> Dict[str, Any]:
        """
        启动辩论
        
        Returns:
            辩论结果字典
        """
        self.start_time = time.time()
        self.status = DebateStatus.ROUND_1
        
        # 初始化Redis
        self._init_redis()
        
        # 通知开始
        self._notify_start()
        
        try:
            # 执行3轮辩论
            for round_num in range(1, 4):
                self._execute_round(round_num)
            
            # 达成共识
            self._reach_consensus()
            
        except Exception as e:
            self._log_error(f"辩论执行失败: {e}")
            raise
        
        finally:
            self.end_time = time.time()
        
        return self.get_result()
    
    def _execute_round(self, round_num: int):
        """执行单轮辩论"""
        self.status = DebateStatus[f"ROUND_{round_num}"]
        self._update_status()
        
        # 并行启动所有专家
        threads = []
        for agent in self.config.agents:
            t = threading.Thread(
                target=self._run_agent,
                args=(agent, round_num)
            )
            t.start()
            threads.append(t)
        
        # 等待所有专家完成（带超时）
        for t in threads:
            t.join(timeout=self.config.timeout_per_round)
        
        # 触发轮次完成回调
        if self.on_round_complete:
            self.on_round_complete(round_num, self._get_round_data(round_num))
    
    def _run_agent(self, agent: Agent, round_num: int):
        """运行单个专家"""
        # 这里应该调用实际的Agent执行逻辑
        # 简化版本：模拟专家思考
        
        # 更新状态：思考中
        self._update_agent_status(agent.name, round_num, 'thinking')
        
        # 模拟思考时间
        time.sleep(1)
        
        # 生成思考内容（实际应该调用sessions_spawn）
        content = self._generate_agent_thought(agent, round_num)
        
        # 保存到Redis
        self._save_thought(agent.name, round_num, content)
        
        # 更新状态：完成
        self._update_agent_status(agent.name, round_num, 'complete')
    
    def _generate_agent_thought(self, agent: Agent, round_num: int) -> str:
        """生成专家思考内容（简化版）"""
        templates = {
            1: f"{agent.name}完成了第1轮分析，提出了初步方案。",
            2: f"{agent.name}回应了其他专家的质疑，进行了补充说明。",
            3: f"{agent.name}做出了妥协，提出了最终立场。"
        }
        return templates.get(round_num, f"{agent.name}的思考内容")
    
    def _reach_consensus(self):
        """达成共识"""
        self.status = DebateStatus.CONSENSUS
        self._update_status()
        
        # 生成共识（实际应该基于各专家Round 3的输出）
        consensus = self._generate_consensus()
        
        # 保存共识
        self.redis.set(
            f"debate:{self.debate_id}:consensus",
            json.dumps(consensus)
        )
        
        # 触发回调
        if self.on_consensus:
            self.on_consensus(consensus)
        
        self.status = DebateStatus.COMPLETED
    
    def _generate_consensus(self) -> Dict:
        """生成共识结果"""
        return {
            'topic': self.topic,
            'debate_id': self.debate_id,
            'elapsed': self._format_elapsed(),
            'decisions': {
                '框架': 'FastAPI 0.100+',
                '认证': 'JWT + Session混合',
                '架构': '渐进分层',
                '工期': '25工作日'
            },
            'compromises': [
                {'agent': a.name, 'content': f'{a.name}做出了适当妥协'}
                for a in self.config.agents
            ],
            'sticking_points': [
                {'agent': a.name, 'content': f'{a.name}坚持了核心原则'}
                for a in self.config.agents
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    def _init_redis(self):
        """初始化Redis存储"""
        # 保存元数据
        meta = {
            'topic': self.topic,
            'agents': json.dumps([a.name for a in self.config.agents]),
            'created_at': datetime.now().isoformat(),
            'status': self.status.value
        }
        self.redis.hset(f"debate:{self.debate_id}:meta", mapping=meta)
    
    def _update_status(self):
        """更新状态到Redis"""
        self.redis.set(
            f"debate:{self.debate_id}:status",
            self.status.value
        )
    
    def _update_agent_status(self, agent_name: str, round_num: int, status: str):
        """更新专家状态"""
        key = f"debate:{self.debate_id}:progress:{agent_name}"
        self.redis.set(key, f"round{round_num}:{status}")
        
        # 发布更新通知
        self.redis.publish(
            f"debate:{self.debate_id}:updates",
            json.dumps({
                'agent': agent_name,
                'round': round_num,
                'status': status,
                'timestamp': time.time()
            })
        )
        
        # 触发更新回调
        if self.on_update:
            self.on_update(agent_name, round_num, status)
    
    def _save_thought(self, agent_name: str, round_num: int, content: str):
        """保存专家思考内容"""
        key = f"debate:{self.debate_id}:round:{round_num}"
        self.redis.hset(key, agent_name, content)
        self.redis.expire(key, 3600)  # 1小时过期
    
    def _get_round_data(self, round_num: int) -> Dict:
        """获取轮次数据"""
        key = f"debate:{self.debate_id}:round:{round_num}"
        return self.redis.hgetall(key)
    
    def _notify_start(self):
        """通知辩论开始"""
        if self.config.enable_notifications and self.config.notification_callback:
            self.config.notification_callback({
                'type': 'start',
                'debate_id': self.debate_id,
                'topic': self.topic,
                'agents': [a.name for a in self.config.agents]
            })
    
    def _log_error(self, message: str):
        """记录错误"""
        self.messages.append({
            'time': datetime.now().isoformat(),
            'type': 'error',
            'message': message
        })
    
    def _format_elapsed(self) -> str:
        """格式化已用时间"""
        if not self.start_time:
            return "N/A"
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        return f"{mins}分{secs}秒"
    
    def get_result(self) -> Dict[str, Any]:
        """
        获取辩论结果
        
        Returns:
            完整的辩论结果
        """
        consensus_data = self.redis.get(f"debate:{self.debate_id}:consensus")
        consensus = json.loads(consensus_data) if consensus_data else {}
        
        return {
            'debate_id': self.debate_id,
            'topic': self.topic,
            'status': self.status.value,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'elapsed': self._format_elapsed(),
            'agents': [{
                'name': a.name,
                'role': a.role.value,
                'description': a.description
            } for a in self.config.agents],
            'rounds': {
                f'round_{i}': self._get_round_data(i)
                for i in range(1, 4)
            },
            'consensus': consensus,
            'messages': self.messages
        }
    
    def cleanup(self):
        """清理辩论数据"""
        pattern = f"debate:{self.debate_id}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)


# 便捷函数
def quick_debate(topic: str, **kwargs) -> Dict[str, Any]:
    """
    快速创建并运行辩论
    
    Args:
        topic: 辩论主题
        **kwargs: 其他参数
    
    Returns:
        辩论结果
    """
    debate = MultiAgentDebate(topic=topic, **kwargs)
    try:
        return debate.start()
    finally:
        debate.cleanup()


# 使用示例
if __name__ == "__main__":
    print("🚀 MultiAgentDebate - 使用示例")
    print("=" * 60)
    
    # 示例1: 使用默认专家
    print("\n示例1: 使用默认专家")
    debate = MultiAgentDebate(
        topic="选择消息队列：Kafka vs RabbitMQ",
        debate_id="demo-001"
    )
    
    # 注册回调
    def on_consensus(result):
        print(f"✅ 达成共识: {result.get('decisions', {})}")
    
    debate.register_callback('consensus', on_consensus)
    
    # 运行
    result = debate.start()
    print(f"\n辩论完成！耗时: {result['elapsed']}")
    print(f"最终决策: {result['consensus'].get('decisions', {})}")
    
    debate.cleanup()
    
    # 示例2: 自定义专家
    print("\n" + "=" * 60)
    print("\n示例2: 自定义专家")
    
    custom_agents = [
        Agent("安全专家", AgentRole.CUSTOM, "网络安全专家", 
              "你专注于安全漏洞分析和防护策略。"),
        Agent("性能专家", AgentRole.CUSTOM, "系统性能专家",
              "你专注于性能优化和瓶颈分析。"),
        Agent("成本专家", AgentRole.CUSTOM, "成本分析专家",
              "你专注于TCO分析和ROI评估。")
    ]
    
    debate2 = MultiAgentDebate(
        topic="选择云服务厂商：AWS vs Azure vs GCP",
        agents=custom_agents,
        debate_id="demo-002"
    )
    
    result2 = debate2.start()
    print(f"\n辩论完成！耗时: {result2['elapsed']}")
    
    debate2.cleanup()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例完成！")
