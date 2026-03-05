#!/usr/bin/env python3
"""
Neural Hub - Feedback Processing System (FPS)
神经中枢反馈处理系统

核心逻辑:
1. 接收输入 (用户请求/小弟反馈/系统事件)
2. 分析内容和上下文
3. 决定处理方式:
   - 简单处理 → 自己快速响应
   - 复杂分析 → Multi-Agent深度思考
   - 需要执行 → 路由给10个小弟
   - 需要修正 → 分配给不同小弟重试
4. 形成闭环
"""

import json
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

class InputSource(Enum):
    USER = "user"           # 用户请求
    NODE_FEEDBACK = "node"  # 小弟反馈
    SYSTEM_EVENT = "system" # 系统事件
    SELF_REFLECTION = "self" # 自我反思

class ProcessingMode(Enum):
    QUICK_RESPONSE = "quick"      # 我快速响应
    DEEP_ANALYSIS = "deep"        # Multi-Agent深度分析
    DELEGATE_EXECUTE = "delegate" # 交给小弟执行
    RETRY_CORRECT = "retry"       # 修正重试
    ROUTE_ANOTHER = "route"       # 转给其他小弟

@dataclass
class NeuralSignal:
    """神经信号 - 需要处理的输入"""
    signal_id: str
    source: InputSource
    content: str
    context: Dict
    timestamp: str
    priority: int = 5  # 1-10, 1最高

class FeedbackProcessor:
    """反馈处理器"""
    
    def __init__(self):
        self.processing_history = []
        self.node_performance = {}  # 记录小弟表现
    
    def analyze_signal(self, signal: NeuralSignal) -> Tuple[ProcessingMode, Optional[str], str]:
        """
        分析信号，决定处理方式
        
        Returns:
            (处理模式, 目标节点(如需要), 原因)
        """
        content = signal.content.lower()
        source = signal.source
        
        # 1. 用户请求 - 常规路由
        if source == InputSource.USER:
            return self._route_user_request(signal)
        
        # 2. 小弟反馈 - 需要分析处理
        if source == InputSource.NODE_FEEDBACK:
            return self._process_node_feedback(signal)
        
        # 3. 系统事件 - 监控告警
        if source == InputSource.SYSTEM_EVENT:
            return self._handle_system_event(signal)
        
        # 4. 自我反思 - 深度分析
        if source == InputSource.SELF_REFLECTION:
            return self._process_self_reflection(signal)
        
        # 默认：自己快速响应
        return (ProcessingMode.QUICK_RESPONSE, None, "默认快速响应")
    
    def _route_user_request(self, signal: NeuralSignal) -> Tuple[ProcessingMode, Optional[str], str]:
        """路由用户请求"""
        content = signal.content
        
        # 检查是否是复杂决策
        if any(kw in content.lower() for kw in ["决定", "选择", "为什么", "分析", "评估"]):
            if len(content) > 100:  # 长文本通常是复杂任务
                return (ProcessingMode.DEEP_ANALYSIS, None, "复杂决策，需要Multi-Agent深度分析")
        
        # 检查是否是执行类任务
        if any(kw in content.lower() for kw in ["搜索", "收集", "获取", "下载", "检查"]):
            return (ProcessingMode.DELEGATE_EXECUTE, "NB02", "数据收集任务，交给data_collector")
        
        if any(kw in content.lower() for kw in ["代码", "测试", "bug", "分析代码"]):
            return (ProcessingMode.DELEGATE_EXECUTE, "NB07", "代码相关，交给code_reviewer")
        
        # 默认：快速响应或交给小弟
        return (ProcessingMode.DELEGATE_EXECUTE, "any", "常规任务，交给小弟执行")
    
    def _process_node_feedback(self, signal: NeuralSignal) -> Tuple[ProcessingMode, Optional[str], str]:
        """处理小弟反馈"""
        content = signal.content
        context = signal.context
        
        node_id = context.get("node_id", "unknown")
        task_status = context.get("status", "unknown")
        
        # 1. 如果执行成功
        if task_status == "success":
            # 检查结果质量
            result_quality = self._assess_result_quality(content)
            
            if result_quality >= 0.8:
                # 高质量结果，自己汇总后返回
                return (ProcessingMode.QUICK_RESPONSE, None, "结果质量高，我汇总后返回")
            else:
                # 质量一般，需要补充分析
                return (ProcessingMode.DEEP_ANALYSIS, None, "结果需要深度分析")
        
        # 2. 如果执行失败
        if task_status == "failed":
            error_type = context.get("error_type", "unknown")
            retry_count = context.get("retry_count", 0)
            
            # 网络错误 → 重试
            if error_type in ["network", "timeout"]:
                if retry_count < 3:
                    return (ProcessingMode.RETRY_CORRECT, node_id, f"网络错误，让{node_id}重试")
                else:
                    # 重试多次失败，换其他小弟
                    alt_node = self._select_alternative_node(node_id)
                    return (ProcessingMode.ROUTE_ANOTHER, alt_node, f"{node_id}多次失败，转给{alt_node}")
            
            # 技能缺失 → 安装skill或转给其他小弟
            if error_type == "skill_not_found":
                skill_name = context.get("missing_skill", "")
                # 检查其他小弟是否有这个skill
                alt_node = self._find_node_with_skill(skill_name)
                if alt_node:
                    return (ProcessingMode.ROUTE_ANOTHER, alt_node, f"转给有{skill_name}的{alt_node}")
                else:
                    # 命令当前小弟安装skill重试
                    return (ProcessingMode.RETRY_CORRECT, node_id, f"命令{node_id}安装{skill_name}后重试")
            
            # 权限错误 → 转给我处理
            if error_type == "permission":
                return (ProcessingMode.DEEP_ANALYSIS, None, "权限问题，我需要分析")
        
        # 3. 如果结果需要进一步处理
        if "需要进一步" in content or "需要验证" in content:
            return (ProcessingMode.DELEGATE_EXECUTE, "NB10", "需要验证，交给quality_assurance")
        
        # 默认：自己快速响应
        return (ProcessingMode.QUICK_RESPONSE, None, "快速响应反馈")
    
    def _handle_system_event(self, signal: NeuralSignal) -> Tuple[ProcessingMode, Optional[str], str]:
        """处理系统事件"""
        event_type = signal.context.get("event_type", "unknown")
        
        # 节点离线
        if event_type == "node_offline":
            node_id = signal.context.get("node_id")
            return (ProcessingMode.QUICK_RESPONSE, None, f"{node_id}离线，我需要处理恢复")
        
        # 安全告警
        if event_type == "security_alert":
            return (ProcessingMode.DEEP_ANALYSIS, None, "安全告警，需要深度分析")
        
        # 资源不足
        if event_type == "resource_low":
            return (ProcessingMode.QUICK_RESPONSE, None, "资源告警，我需要调整")
        
        # 默认：监控即可
        return (ProcessingMode.QUICK_RESPONSE, None, "常规系统事件")
    
    def _process_self_reflection(self, signal: NeuralSignal) -> Tuple[ProcessingMode, Optional[str], str]:
        """处理自我反思"""
        # 自我反思通常是深度分析
        return (ProcessingMode.DEEP_ANALYSIS, None, "自我反思需要深度分析")
    
    def _assess_result_quality(self, content: str) -> float:
        """评估结果质量 0-1"""
        # 简单的质量评估
        quality = 0.5
        
        # 有具体数据 → 高质量
        if any(kw in content for kw in ["数据", "结果", "发现", "统计"]):
            quality += 0.2
        
        # 有详细分析 → 高质量
        if len(content) > 200:
            quality += 0.1
        
        # 有结论 → 高质量
        if "结论" in content or "总结" in content:
            quality += 0.1
        
        # 有错误 → 降低质量
        if "错误" in content or "失败" in content:
            quality -= 0.3
        
        return min(max(quality, 0), 1)
    
    def _select_alternative_node(self, failed_node: str) -> str:
        """选择替代节点"""
        # 简单策略：选择同组的另一个节点
        node_groups = {
            "step": ["NB01", "NB02", "NB03", "NB04", "NB05"],
            "ds": ["NB06", "NB07", "NB08", "NB09", "NB10"]
        }
        
        for group, nodes in node_groups.items():
            if failed_node in nodes:
                # 选择同组的下一个节点
                idx = nodes.index(failed_node)
                alt_idx = (idx + 1) % len(nodes)
                return nodes[alt_idx]
        
        return "NB01"  # 默认
    
    def _find_node_with_skill(self, skill_name: str) -> Optional[str]:
        """查找有特定skill的节点"""
        # 这里应该从实际配置中查询
        # 简化版：返回NB02 (数据收集，skill最多)
        skill_mapping = {
            "web_search": ["NB01", "NB02"],
            "github": ["NB04"],
            "agent_reach": ["NB02", "NB09"],
        }
        nodes = skill_mapping.get(skill_name, [])
        return nodes[0] if nodes else None
    
    def process(self, signal: NeuralSignal) -> Dict:
        """处理信号的主入口"""
        mode, target, reason = self.analyze_signal(signal)
        
        result = {
            "signal_id": signal.signal_id,
            "input_source": signal.source.value,
            "processing_mode": mode.value,
            "target_node": target,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        # 记录历史
        self.processing_history.append(result)
        
        return result

# 示例
def demo():
    """演示反馈处理"""
    processor = FeedbackProcessor()
    
    test_signals = [
        # 1. 用户请求
        NeuralSignal(
            signal_id="sig_001",
            source=InputSource.USER,
            content="帮我搜索最新的AI论文",
            context={},
            timestamp=datetime.now().isoformat()
        ),
        
        # 2. 小弟成功反馈
        NeuralSignal(
            signal_id="sig_002",
            source=InputSource.NODE_FEEDBACK,
            content="已找到10篇相关论文，数据如下...",
            context={"node_id": "NB02", "status": "success"},
            timestamp=datetime.now().isoformat()
        ),
        
        # 3. 小弟失败反馈
        NeuralSignal(
            signal_id="sig_003",
            source=InputSource.NODE_FEEDBACK,
            content="执行失败，网络超时",
            context={"node_id": "NB02", "status": "failed", "error_type": "timeout", "retry_count": 2},
            timestamp=datetime.now().isoformat()
        ),
        
        # 4. 系统事件
        NeuralSignal(
            signal_id="sig_004",
            source=InputSource.SYSTEM_EVENT,
            content="NB03离线超过30秒",
            context={"event_type": "node_offline", "node_id": "NB03"},
            timestamp=datetime.now().isoformat()
        ),
    ]
    
    print("=" * 70)
    print("🧠 神经中枢反馈处理演示")
    print("=" * 70)
    
    for signal in test_signals:
        print(f"\n📥 输入: [{signal.source.value}] {signal.content[:40]}...")
        result = processor.process(signal)
        print(f"📤 处理: {result['processing_mode']}")
        if result['target_node']:
            print(f"   目标: {result['target_node']}")
        print(f"   原因: {result['reason']}")

if __name__ == "__main__":
    demo()
