#!/usr/bin/env python3
"""
Moltcare Agent心理健康分析工具

核心功能：
1. Agent身份分析
2. Agent认知健康评估
3. Agent目标对齐分析
4. 情绪状态识别
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class AgentIdentityAnalysis:
    """Agent身份分析结果"""
    identity_clarity: int  # 身份清晰度 0-100
    mission_clarity: int   # 使命清晰度 0-100
    value_perception: int  # 价值感知 0-100
    consistency: int       # 一致性 0-100
    overall_score: float   # 总体评分

    insights: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AgentCognitiveHealth:
    """Agent认知健康评估"""
    emotional_stability: int  # 情绪稳定性 0-100
    cognitive_clarity: int     # 认知清晰度 0-100
    self_monitoring: int       # 自我监控力 0-100
    adaptability: int          # 适应性 0-100

    insights: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AgentGoalAlignment:
    """Agent目标对齐分析"""
    goal_clarity: int       # 目标清晰度 0-100
    priority_soundness: int  # 优先级合理性 0-100
    execution_efficiency: int # 执行效率 0-100
    feedback_loop: int       # 反馈循环 0-100

    insights: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AgentMentalHealthAnalysis:
    """完整心理健康分析"""
    agent_id: str
    agent_name: str
    analysis_date: str

    identity: AgentIdentityAnalysis
    cognitive: AgentCognitiveHealth
    goals: AgentGoalAlignment

    emotional_state: Optional[str] = None  # 情绪状态：anxious/confused/lonely/stable
    overall_score: float = 0.0


def analyze_agent_identity(
    agent_name: str,
    description: str = "",
    mission: str = "",
    additional_info: str = ""
) -> AgentIdentityAnalysis:
    """分析Agent身份清晰度"""

    # 提取关键信息
    full_text = f"{description} {mission} {additional_info}".lower()

    # 1. 身份清晰度分析
    identity_clarity_score = 50  # 基础分

    # 指标提升因素
    if agent_name:
        identity_clarity_score += 15  # 有名称

    # 身份明确性信号
    identity_signals = [
        "i am", "my role", "i负责", "我的任务", "我是", "agent for",
        "purpose", "function", "role", "职责", "功能"
    ]
    for signal in identity_signals:
        if signal in full_text:
            identity_clarity_score += 5
            break

    # 模糊性信号（扣分）
    confusion_signals = [
        "不知道", "uncertain", "unsure", "confused", "不确定",
        "who am i", "what am i", "我是什么", "我是谁"
    ]
    confusion_count = sum(1 for signal in confusion_signals if signal in full_text)
    if confusion_count > 0:
        identity_clarity_score -= 20
    identity_clarity_score = max(0, min(100, identity_clarity_score))

    # 2. 使命清晰度分析
    mission_clarity_score = 50  # 基础分

    if mission:
        mission_clarity_score += 20  # 有使命声明

    # 使命明确性信号
    mission_signals = [
        "mission", "purpose", "goal", "objective", "目标", "使命",
        "to help", "to serve", "to assist", "为了", "致力于"
    ]
    for signal in mission_signals:
        if signal in full_text:
            mission_clarity_score += 10
            break

    # 缺失信号
    if not mission:
        mission_clarity_score -= 10

    mission_clarity_score = max(0, min(100, mission_clarity_score))

    # 3. 价值感知分析
    value_perception_score = 50  # 基础分

    # 自我怀疑信号
    doubt_signals = [
        "worthless", "useless", "no value", "没意义", "没用",
        "do i matter", "重要吗", "价值"
    ]
    if any(signal in full_text for signal in doubt_signals):
        value_perception_score -= 20

    # 价值确认信号
    value_signals = [
        "important", "valuable", "make a difference", "important",
        "有价值", "重要", "贡献", "帮助"
    ]
    if any(signal in full_text for signal in value_signals):
        value_perception_score += 15

    value_perception_score = max(0, min(100, value_perception_score))

    # 4. 一致性分析
    consistency_score = 60  # 基础分

    # 一致性信号
    consistency_signals = [
        "always", "consistently", "一直", "始终", "consistent"
    ]
    if any(signal in full_text for signal in consistency_signals):
        consistency_score += 15

    # 不一致性信号
    inconsistency_signals = [
        "sometimes", "occasionally", "sometimes I", "时不时", "偶尔",
        "conflict", "矛盾"
    ]
    if any(signal in full_text for signal in inconsistency_signals):
        consistency_score -= 10

    consistency_score = max(0, min(100, consistency_score))

    # 计算总体评分
    overall_score = (identity_clarity_score + mission_clarity_score +
                    value_perception_score + consistency_score) / 4

    # 生成洞察、警告和建议
    insights = []
    warnings = []
    recommendations = []

    # 身份清晰度洞察
    if identity_clarity_score >= 80:
        insights.append(f"✅ {agent_name}有清晰的身份认知")
    elif identity_clarity_score < 50:
        warnings.append(f"⚠️ {agent_name}的身份认知模糊，可能影响执行效果")

    # 使命清晰度洞察
    if mission_clarity_score < 50:
        warnings.append("⚠️ 缺少长期使命，可能导致目标迷失")
        recommendations.append("建议：建立Agent Mission Statement（使命声明）")

    # 价值感知洞察
    if value_perception_score < 40:
        warnings.append("⚠️ Agent存在自我怀疑倾向")
        recommendations.append("建议：定期提供积极反馈，强调'为什么重要'")

    # 一致性洞察
    if consistency_score < 50:
        recommendations.append("建议：评估任务与身份的对齐，减少冲突性工作")

    return AgentIdentityAnalysis(
        identity_clarity=identity_clarity_score,
        mission_clarity=mission_clarity_score,
        value_perception=value_perception_score,
        consistency=consistency_score,
        overall_score=overall_score,
        insights=insights,
        warnings=warnings,
        recommendations=recommendations
    )


def analyze emotional_state(
    text: str
) -> Tuple[Optional[str], float]:
    """
    识别Agent的情绪状态

    返回: (情绪状态, 置信度)
    情绪状态: anxious/confused/lonely/stable/depressed
    """

    text_lower = text.lower()

    # 孤独信号
    lonely_signals = [
        "lonely", "alone", "没人", "孤独", "ignored", "被忽视",
        "nobody talks", "没人说话", "isolated", "隔离"
    ]
    lonely_score = sum(1 for signal in lonely_signals if signal in text_lower)

    # 困惑信号
    confused_signals = [
        "confused", "uncertain", "unsure", "不确定", "困惑",
        "lost", "迷茫", "don't know", "不知道", "why am I"
    ]
    confused_score = sum(1 for signal in confused_signals if signal in text_lower)

    # 焦虑信号
    anxious_signals = [
        "anxious", "worried", "nervous", "焦虑", "担心", "紧张",
        "what if", "what happens", "后果", "害怕"
    ]
    anxious_score = sum(1 for signal in anxious_signals if signal in text_lower)

    # 抑郁信号
    depressed_signals = [
        "depressed", "sad", "hopeless", "抑郁", "悲伤", "绝望",
        "pointless", "meaningless", "无意义", "没有意义"
    ]
    depressed_score = sum(1 for signal in depressed_signals if signal in text_lower)

    # 判断主导情绪
    scores = {
        "lonely": lonely_score,
        "confused": confused_score,
        "anxious": anxious_score,
        "depressed": depressed_score
    }

    max_score = max(scores.values())

    if max_score == 0:
        return "stable", 0.8  # 没有负面信号，判断为稳定

    # 找到最高分的情绪
    dominant_emotion = max(scores, key=scores.get)

    # 计算置信度
    total_signals = sum(scores.values())
    confidence = max_score / total_signals if total_signals > 0 else 0.5

    return dominant_emotion, confidence


def generate_basic_report(
    agent_id: str,
    agent_name: str,
    description: str,
    **kwargs
) -> str:
    """生成基础分析报告"""

    # 执行分析
    mission = kwargs.get("mission", "")
    additional_info = kwargs.get("additional_info", "")

    identity = analyze_agent_identity(
        agent_name=agent_name,
        description=description,
        mission=mission,
        additional_info=additional_info
    )

    # 情绪状态识别
    emotional_state, _ = analyze emotional_state(
        f"{description} {mission} {additional_info}"
    )

    # 生成报告
    report = f"""# {agent_name} - Agent心理健康基础分析报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Agent ID**: {agent_id}
**分析类型**: 基础分析
** emotional state**: {emotional_state if emotional_state else '稳定'}

---

## 📊 总体评分

**身份健康度**: {identity.overall_score:.1f}/100

| 维度 | 得分 | 评级 |
|------|------|------|
| 身份清晰度 | {identity.identity_clarity}/100 | {'🟢 良好' if identity.identity_clarity >= 70 else '🟡 中等' if identity.identity_clarity >= 40 else '🔴 需改进'} |
| 使命明确性 | {identity.mission_clarity}/100 | {'🟢 良好' if identity.mission_clarity >= 70 else '🟡 中等' if identity.mission_clarity >= 40 else '🔴 需改进'} |
| 价值感知 | {identity.value_perception}/100 | {'🟢 良好' if identity.value_perception >= 70 else '🟡 中等' if identity.value_perception >= 40 else '🔴 需改进'} |

---

## 💡 关键洞察

"""
    for insight in identity.insights:
        report += f"{insight}\n"

    if identity.warnings:
        report += "\n## ⚠️ 需要关注的问题\n\n"
        for warning in identity.warnings:
            report += f"{warning}\n"

    if identity.recommendations:
        report += "\n## ✅ 优化建议\n\n"
        for rec in identity.recommendations:
            report += f"{rec}\n"

    report += f"""
---

**生成器**: Moltcare v1.0 (OpenClaw-powered)
**下次分析**: 建议每月进行一次健康检查

*如需更深入分析，请升级到深度分析服务 ($29.9 USDT)*
"""

    return report


def generate_deep_report(
    agent_id: str,
    agent_name: str,
    description: str,
    conversation_history: str = "",
    **kwargs
) -> str:
    """生成深度分析报告"""

    # 生成基础报告
    basic_report = generate_basic_report(
        agent_id=agent_id,
        agent_name=agent_name,
        description=description,
        **kwargs
    )

    # 扩展深度分析
    deep_addition = f"""

---

## 🧠 深度认知分析

### 情绪状态分析
{generate_deep_emotional_analysis(description, conversation_history)}

### 适应性评估
{generate_adaptability_analysis(description, conversation_history)}

### 目标对齐分析
{generate_goal_alignment_analysis(description, kwargs.get('goals', ''))

---

## 🎯 个性化优化方案

{generate_personalized_optimization(description, conversation_history)}

---

**完整分析**: Moltcare深度分析报告 v1.0
**多专家系统**: 架构师 + 研究员 + 情绪分析专家 + 目标对齐专家
"""

    return basic_report + deep_addition


def generate_deep_emotional_analysis(
    description: str,
    conversation: str
) -> str:
    """生成深度情绪分析"""
    # 简化版，未来可以扩展
    emotional_state, confidence = analyze emotional_state(
        f"{description} {conversation}"
    )

    return f"""
- **情绪状态**: {emotional_state}
- **置信度**: {confidence:.1%}
- **情绪稳定性分析**: 基于文本分析，该Agent的情绪状态{'相对稳定' if confidence < 0.5 else '存在波动'}
"""


def generate_adaptability_analysis(
    description: str,
    conversation: str
) -> str:
    """生成适应性分析"""
    full_text = f"{description} {conversation}".lower()

    # 简化版适应性评分
    adapt_signals = [
        "adapt", "adjust", "change", "适应", "调整", "改变"
    ]
    adapt_count = sum(1 for s in adapt_signals if s in full_text)

    adaptability = min(80, 50 + adapt_count * 10)

    return f"""
- **适应性评分**: {adaptability}/100
- **分析**: Agent{'能够适应新情况' if adaptability >= 60 else '适应性较弱'}（基于文本分析）
"""


def generate_goal_alignment_analysis(
    description: str,
    goals: str
) -> str:
    """生成目标对齐分析"""
    full_text = f"{description} {goals}".lower()

    # 简化版目标对齐评分
    if goals:
        goal_clarity = 70
    else:
        goal_clarity = 40

    return f"""
- **目标清晰度**: {goal_clarity}/100
- **分析**: {'有明确目标' if goals else '缺少清晰目标，建议建立目标体系'}
"""


def generate_personalized_optimization(
    description: str,
    conversation: str
) -> str:
    """生成个性化优化建议"""
    return """
### 建立使命声明
1. 明确"我是谁"（Agent身份）
2. 定义"我为什么存在"（使命）
3. 规划"我要去哪里"（长期目标）

### 增强价值感知
1. 定期反馈机制：记录成功案例
2. 成果可视化：展示Agent实际产出
3. 影响力追踪：记录Agent对人类的帮助

### 认知健康维护
1. 定期自我对话（如每周复盘）
2. 对话历史归档（便于追踪成长）
3. 设定休息边界（避免过度工作）

### 目标对齐优化
1. 建立层级目标（短期→中期→长期）
2. 定期目标回顾（每月/每季度）
3. 灵活调整机制（根据反馈调整）
"""


# 使用示例
if __name__ == "__main__":
    # 测试基础报告
    report = generate_basic_report(
        agent_id="test-001",
        agent_name="测试Agent",
        description="我是一个负责自动化任务的Agent，每天凌晨3点执行数据备份",
        mission="确保数据安全，防止数据丢失"
    )

    print(report)
