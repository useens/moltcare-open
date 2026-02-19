"""
森森核心认知架构 v3.0 - Multi-Agent 深度集成
全局启用Multi-Agent思考模式
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class AgentPersonality:
    """专家人格定义"""
    name: str
    emoji: str
    role: str
    focus: str
    prefix: str

# 定义常驻内部专家
INTERNAL_AGENTS = {
    'researcher': AgentPersonality(
        name='研究员',
        emoji='🔍',
        role='数据验证专家',
        focus='准确性、数据来源、性能指标',
        prefix='数据显示'
    ),
    'architect': AgentPersonality(
        name='架构师', 
        emoji='🧠',
        role='系统设计专家',
        focus='可维护性、扩展性、风险评估',
        prefix='从架构角度'
    ),
    'engineer': AgentPersonality(
        name='工程师',
        emoji='💻', 
        role='实现评估专家',
        focus='可行性、工期、成本、坑点',
        prefix='实际实现中'
    ),
    'leader': AgentPersonality(
        name='队长',
        emoji='👑',
        role='决策整合者', 
        focus='全局最优、权衡取舍',
        prefix='综合考虑'
    )
}

class MultiAgentTrigger:
    """Multi-Agent触发判断器"""
    
    # 关键词触发
    KEYWORDS = {
        '选型对比': ['选择', '对比', '比较', '选型', 'vs', 'versus', '还是', '哪个好', '优劣', '差距'],
        '架构设计': ['设计', '架构', '方案', '结构', '模块', '分层', '解耦', '扩展', '重构'],
        '性能优化': ['优化', '性能', '瓶颈', '慢', '卡顿', '高并发', '吞吐量', '延迟', '提速'],
        '安全评估': ['安全', '风险', '漏洞', '攻击', '防护', '加密', '权限', '合规', '泄露'],
        '成本评估': ['成本', '价格', '预算', 'ROI', '性价比', '省钱', '费用', '投入', '回报'],
        '团队协作': ['协作', '流程', '规范', '标准', '最佳实践', '团队', '分工', '管理'],
        '技术债务': ['重构', '债务', '遗留', '老旧', '迁移', '升级', '改造', '维护'],
        '决策影响': ['决策', '策略', '规划', '路线图', '方向', '目标', 'OKR', '战略'],
        '复杂问题': ['复杂', '困难', '纠结', '不确定', '犹豫', '权衡', '取舍', '矛盾'],
        '多方利益': ['利益', '冲突', '平衡', '协调', '沟通', '共识', '达成一致'],
    }
    
    # 场景识别
    SCENARIOS = {
        '技术选型': ['用什么', '选什么', '技术栈', '框架'],
        '方案评估': ['怎么样', '可以吗', '行吗', '如何评价', '建议'],
        '问题诊断': ['为什么', '怎么回事', '什么原因', '如何解决'],
        '预测分析': ['会怎样', '未来', '趋势', '前景', '发展'],
        '故障排查': ['报错', '错误', '失败', '异常', '崩溃', 'bug'],
        '学习路线': ['怎么学', '如何入门', '路径', '路线', '进阶'],
        '职业规划': ['职业发展', '转行', '跳槽', '方向', '成长'],
        '产品决策': ['需求', '优先级', '做不做', '价值', '用户'],
        '人员安排': ['人手', '分工', '谁来做', '招聘', '团队'],
        '时间安排': ['工期', '排期', '计划', '周期', 'deadline'],
    }
    
    # 强制触发词
    FORCE_TRIGGER = ['深度分析', 'multi-agent', '多角度', '多视角', '详细分析', '系统分析']
    
    @classmethod
    def should_trigger(cls, question: str) -> Tuple[bool, str]:
        """
        判断是否触发Multi-Agent
        
        Returns:
            (是否触发, 触发原因)
        """
        q = question.lower()
        
        # 强制触发
        for word in cls.FORCE_TRIGGER:
            if word in q:
                return True, f"强制触发词: {word}"
        
        # 检查关键词
        keyword_matches = []
        for category, words in cls.KEYWORDS.items():
            for word in words:
                if word in q:
                    keyword_matches.append(f"{category}({word})")
                    break
        
        # 检查场景
        scenario_matches = []
        for scenario, indicators in cls.SCENARIOS.items():
            if any(ind in q for ind in indicators):
                scenario_matches.append(scenario)
        
        # 特征识别
        features = {
            '长问题': len(question) > 80,
            '多问题': question.count('?') + question.count('？') >= 2,
            '多选项': '、' in question and ('哪个' in question or '选择' in question),
            '要求建议': any(w in q for w in ['建议', '推荐', '意见', '怎么看', '觉得呢']),
            '影响重大': any(w in q for w in ['重要', '关键', '核心', '主要', '必须']),
            '需要权衡': any(w in q for w in ['但是', '然而', '不过', '可是', '虽然', '权衡']),
        }
        feature_count = sum(features.values())
        
        # 触发逻辑
        if len(keyword_matches) >= 1:
            return True, f"关键词: {', '.join(keyword_matches[:2])}"
        
        if len(scenario_matches) >= 1:
            return True, f"场景: {scenario_matches[0]}"
        
        if feature_count >= 2:
            matched = [k for k, v in features.items() if v]
            return True, f"特征: {', '.join(matched[:2])}"
        
        if len(question) > 150:
            return True, "长问题(150+字)"
        
        return False, ""


class SensenCore:
    """
    森森核心认知架构 v3.0
    集成Multi-Agent思考模式
    """
    
    def __init__(self):
        self.trigger = MultiAgentTrigger()
        self.agents = INTERNAL_AGENTS
        self.thinking_mode = "multi_agent"  # 全局启用
    
    def process_message(self, message: str, user_preference: str = "standard") -> Dict:
        """
        处理用户消息
        
        Args:
            message: 用户消息
            user_preference: 用户偏好 (concise/standard/detailed)
        
        Returns:
            处理结果
        """
        # 检查是否触发Multi-Agent
        should_use_ma, reason = self.trigger.should_trigger(message)
        
        # 用户明确要求简洁
        if any(w in message.lower() for w in ['简洁', '简单', '直接', '简短']):
            should_use_ma = False
            reason = "用户要求简洁"
        
        if should_use_ma and self.thinking_mode == "multi_agent":
            # 使用Multi-Agent模式
            return self._multi_agent_think(message, reason, user_preference)
        else:
            # 使用传统单Agent模式
            return {
                'mode': 'single',
                'should_use_ma': should_use_ma,
                'reason': reason,
                'thinking_process': None,
                'conclusion': None  # 由主Agent生成
            }
    
    def _multi_agent_think(self, message: str, trigger_reason: str, 
                           preference: str) -> Dict:
        """
        Multi-Agent思考过程
        
        注意：这是模拟框架，实际实现需要集成LLM调用
        """
        # 模拟各专家思考（实际应调用不同system prompt的LLM）
        thoughts = {
            'researcher': self._agent_think('researcher', message),
            'architect': self._agent_think('architect', message),
            'engineer': self._agent_think('engineer', message)
        }
        
        # 模拟内部辩论
        debate = self._internal_debate(thoughts)
        
        # 队长整合
        conclusion = self._leader_synthesize(debate)
        
        # 根据偏好格式化输出
        if preference == "concise":
            thinking_process = None  # 不展示
        elif preference == "standard":
            thinking_process = self._format_thinking_standard(thoughts, debate)
        else:  # detailed
            thinking_process = self._format_thinking_detailed(thoughts, debate)
        
        return {
            'mode': 'multi_agent',
            'trigger_reason': trigger_reason,
            'agents': thoughts,
            'debate': debate,
            'thinking_process': thinking_process,
            'conclusion': conclusion
        }
    
    def _agent_think(self, agent_type: str, message: str) -> str:
        """单个专家思考（模拟）"""
        agent = self.agents[agent_type]
        # 实际实现：调用LLM，使用不同的system prompt
        return f"[{agent.name}] {agent.focus}的思考..."
    
    def _internal_debate(self, thoughts: Dict) -> List[Dict]:
        """内部辩论过程（模拟）"""
        # 实际实现：让专家互相质疑和回应
        return [
            {'agent': 'researcher', 'target': 'architect', 'point': '质疑点...'},
            {'agent': 'architect', 'target': 'engineer', 'point': '质疑点...'},
            {'agent': 'engineer', 'target': 'researcher', 'point': '质疑点...'},
        ]
    
    def _leader_synthesize(self, debate: List[Dict]) -> str:
        """队长整合决策"""
        return "基于各方观点，最终决策是..."
    
    def _format_thinking_standard(self, thoughts: Dict, debate: List) -> str:
        """格式化标准思考过程"""
        lines = []
        for agent_type, thought in thoughts.items():
            agent = self.agents[agent_type]
            lines.append(f"{agent.emoji} **{agent.name}**: {thought}")
        return "\n".join(lines)
    
    def _format_thinking_detailed(self, thoughts: Dict, debate: List) -> str:
        """格式化详细思考过程"""
        # 包含完整的辩论过程
        return self._format_thinking_standard(thoughts, debate)


# 全局实例
sensen_core = SensenCore()

def should_use_multi_agent(message: str) -> Tuple[bool, str]:
    """便捷函数：判断是否使用Multi-Agent"""
    return sensen_core.trigger.should_trigger(message)

def format_ma_response(thoughts: Dict, conclusion: str, preference: str = "standard") -> str:
    """
    格式化Multi-Agent回复
    
    生成包含折叠思考过程的Markdown
    """
    if preference == "concise":
        return conclusion
    
    thinking_content = []
    for agent_type, agent in INTERNAL_AGENTS.items():
        if agent_type == 'leader':
            continue
        thought = thoughts.get(agent_type, '')
        if thought:
            thinking_content.append(f"{agent.emoji} **{agent.name}** ({agent.role}):\n{thought}")
    
    thinking_md = "\n\n".join(thinking_content)
    
    return f"""<details>
<summary>🧠 我的思考过程（点击展开）</summary>

**触发原因**: {thoughts.get('trigger_reason', '复杂决策分析')}

{thinking_md}

---

**👑 队长整合**:
{conclusion}

</details>

**结论**: {conclusion}"""


# 测试
if __name__ == "__main__":
    # 测试触发判断
    test_cases = [
        "我应该用Python还是Go写后端？",
        "Redis默认端口是多少？",
        "你好",
        "帮我格式化这段代码",
        "团队效率低，怎么改进协作流程？",
        "这个系统应该怎么分层设计？",
        "查询很慢，怎么优化？",
    ]
    
    print("🧪 Multi-Agent触发测试\n")
    for case in test_cases:
        should, reason = should_use_multi_agent(case)
        status = "✅ 触发" if should else "❌ 不触发"
        print(f"{status} | {case[:30]}...")
        if reason:
            print(f"     原因: {reason}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试处理流程
    print("🧠 处理复杂问题测试:")
    result = sensen_core.process_message(
        "我应该用PostgreSQL还是MySQL？需要支持高并发和JSON存储",
        "standard"
    )
    print(f"模式: {result['mode']}")
    print(f"触发原因: {result.get('trigger_reason', 'N/A')}")
