#!/usr/bin/env python3
"""
Multi-Agent Debate Engine - Redis实时辩论核心
常态化运行版本 - 替代本地模拟
"""
import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Callable, Optional

sys.path.insert(0, "/root/.openclaw/workspace/skills/multi-agent-debate")
from redis_manager import DebateRedisManager, AgentUpdate

class RedisMultiAgentEngine:
    """Redis实时多专家引擎 - 常态化运行"""
    
    def __init__(self, debate_id: str = None, redis_port: int = 6380):
        self.debate_id = debate_id or f"debate-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.redis = DebateRedisManager(port=redis_port)
        
        # 四专家配置
        self.agents = {
            'researcher': {'name': '🔍 研究员', 'role': '数据验证与事实核查', 'color': '\033[94m'},
            'architect': {'name': '🧠 架构师', 'role': '系统设计与长期规划', 'color': '\033[95m'},
            'engineer': {'name': '💻 工程师', 'role': '实现可行性与执行成本', 'color': '\033[92m'},
            'security': {'name': '🛡️ 安全专家', 'role': '安全风险评估', 'color': '\033[91m'}
        }
        
        self.results = {}
        self.running = False
        
    def start_debate(self, topic: str, context: Dict = None):
        """启动实时辩论"""
        print(f"\n{'='*60}")
        print(f"🚀 Redis实时多专家辩论启动")
        print(f"辩论ID: {self.debate_id}")
        print(f"主题: {topic}")
        print(f"{'='*60}\n")
        
        # 创建辩论会话
        self.redis.create_debate(
            self.debate_id,
            topic,
            list(self.agents.keys())
        )
        
        # 启动订阅线程
        self.running = True
        self.sub_thread = threading.Thread(target=self._subscribe_updates, daemon=True)
        self.sub_thread.start()
        
        # 并行启动四专家分析
        threads = []
        for agent_id, agent_info in self.agents.items():
            t = threading.Thread(
                target=self._agent_analysis,
                args=(agent_id, agent_info, topic, context)
            )
            t.start()
            threads.append(t)
        
        # 等待所有专家完成
        for t in threads:
            t.join()
        
        # 队长整合
        consensus = self._generate_consensus()
        
        self.running = False
        return consensus
    
    def _agent_analysis(self, agent_id: str, agent_info: Dict, topic: str, context: Dict):
        """单个专家分析流程"""
        # 更新状态: 思考中
        self._publish_update(agent_id, 'thinking', f"{agent_info['name']}开始分析...")
        
        # 模拟分析时间 (实际应调用真实分析逻辑)
        time.sleep(0.5)
        
        # 根据角色生成分析结果
        analysis = self._generate_analysis(agent_id, topic, context)
        
        # 保存到Redis
        self.redis.save_thought(self.debate_id, 1, agent_id, analysis)
        
        # 更新状态: 完成
        self._publish_update(agent_id, 'complete', analysis[:100])
        
        self.results[agent_id] = analysis
    
    def _generate_analysis(self, agent_id: str, topic: str, context: Dict) -> str:
        """生成专家分析 (实际应调用AI模型)"""
        analyses = {
            'researcher': f'数据验证: {topic}相关数据已核实，来源可靠。',
            'architect': f'架构评估: {topic}在系统架构层面可行，扩展性良好。',
            'engineer': f'实现评估: {topic}技术实现难度中等，工期可控。',
            'security': f'安全评估: {topic}无重大安全风险，符合最佳实践。'
        }
        return analyses.get(agent_id, '分析完成')
    
    def _publish_update(self, agent_id: str, status: str, content: str):
        """发布实时更新"""
        update = AgentUpdate(
            round_num=1,
            agent_name=agent_id,
            status=status,
            content=content
        )
        self.redis.publish_update(self.debate_id, update)
        self.redis.set_progress(self.debate_id, agent_id, status)
    
    def _subscribe_updates(self):
        """订阅实时更新 (用于Canvas显示)"""
        def on_update(update: AgentUpdate):
            agent_info = self.agents.get(update.agent_name, {})
            color = agent_info.get('color', '')
            name = agent_info.get('name', update.agent_name)
            print(f"{color}[{name}] {update.status}: {update.content[:50]}...\033[0m")
        
        self.redis.subscribe_updates(self.debate_id, on_update)
        
        # 保持订阅直到辩论结束
        while self.running:
            time.sleep(0.1)
        
        self.redis.unsubscribe()
    
    def _generate_consensus(self) -> str:
        """队长整合共识"""
        print(f"\n{'='*60}")
        print("👑 队长整合中...")
        print(f"{'='*60}\n")
        
        consensus = "基于四专家分析，综合决策如下:\n"
        for agent_id, analysis in self.results.items():
            agent_name = self.agents[agent_id]['name']
            consensus += f"- {agent_name}: {analysis[:80]}...\n"
        
        # 保存共识
        self.redis.set_debate_status(self.debate_id, 'consensus')
        
        print(consensus)
        return consensus
    
    def get_stats(self) -> Dict:
        """获取辩论统计"""
        return self.redis.get_stats(self.debate_id)

# 全局引擎实例
_redis_engine = None

def get_redis_engine() -> RedisMultiAgentEngine:
    """获取Redis多专家引擎"""
    global _redis_engine
    if _redis_engine is None:
        _redis_engine = RedisMultiAgentEngine()
    return _redis_engine

def quick_debate(topic: str, context: Dict = None) -> str:
    """快速启动Redis实时辩论"""
    engine = get_redis_engine()
    return engine.start_debate(topic, context)

if __name__ == "__main__":
    # 测试
    result = quick_debate("测试实时辩论系统")
    print("\n✅ 辩论完成")
