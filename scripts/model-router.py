#!/usr/bin/env python3
"""
双模型智能路由系统
根据任务特征自动选择 Kimi K2.5 或 Nemotron-Nano
"""

import re
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class TaskType(Enum):
    GREETING = "greeting"
    CODE = "code_generation"
    ANALYSIS = "analysis"
    SHORT_QUERY = "short_query"
    LONG_CONTEXT = "long_context"
    REASONING = "reasoning_task"
    SYSTEM_CHECK = "system_check"
    UNKNOWN = "unknown"

@dataclass
class RoutingDecision:
    model: str
    alias: str
    reason: str
    confidence: float
    estimated_cost: float

class ModelRouter:
    """模型路由器 - 智能选择最优模型"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.lightweight_patterns = self._compile_patterns(
            self.config.get('lightweight_patterns', [])
        )
        self.deep_patterns = self._compile_patterns(
            self.config.get('deep_patterns', [])
        )
    
    def _load_config(self, config_path: str = None) -> Dict:
        """加载路由配置"""
        if config_path is None:
            config_path = Path.home() / '.openclaw' / 'workspace' / 'config' / 'model-routing.yaml'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  无法加载配置: {e}", file=sys.stderr)
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'models': {
                'primary': {'id': 'kimi-coding/k2p5', 'alias': 'Kimi K2.5'},
                'lightweight': {'id': 'nvidia/nemotron-nano', 'alias': 'Nemotron-Nano'}
            },
            'routing_strategy': {'default': 'primary'}
        }
    
    def _compile_patterns(self, patterns: List[Dict]) -> List[Tuple[re.Pattern, Dict]]:
        """编译正则表达式模式"""
        compiled = []
        for p in patterns:
            if 'pattern' in p:
                try:
                    compiled.append((re.compile(p['pattern'], re.IGNORECASE), p))
                except re.error:
                    continue
        return compiled
    
    def analyze_task(self, query: str, context_length: int = 0) -> Dict:
        """分析任务特征"""
        analysis = {
            'is_code_related': bool(re.search(r'(代码|程序|脚本|code|function|class|def)', query, re.I)),
            'is_analysis': bool(re.search(r'(分析|深度|详细|架构|设计|analyze|design)', query, re.I)),
            'is_short': len(query) < 50,
            'is_greeting': bool(re.search(r'^(你好|嗨|Hello|Hi|嘿|在吗)', query, re.I)),
            'is_system_check': bool(re.search(r'(HEARTBEAT|心跳|状态|status)', query, re.I)),
            'context_length': context_length,
            'has_complex_reasoning': bool(re.search(r'(为什么|如何|解释|why|how|explain).*(原理|机制|concept)', query, re.I))
        }
        return analysis
    
    def route(self, query: str, context_length: int = 0, force_model: str = None) -> RoutingDecision:
        """
        智能路由决策
        
        返回: RoutingDecision 包含选择的模型和理由
        """
        models = self.config.get('models', {})
        primary = models.get('primary', {'id': 'kimi-coding/k2p5', 'alias': 'Kimi K2.5'})
        lightweight = models.get('lightweight', {'id': 'nvidia/nemotron-nano', 'alias': 'Nemotron-Nano'})
        
        # 强制指定模型
        if force_model:
            if force_model in ['lightweight', 'nano', 'nemotron']:
                return RoutingDecision(
                    model=lightweight['id'],
                    alias=lightweight['alias'],
                    reason="用户强制指定轻量模型",
                    confidence=1.0,
                    estimated_cost=0.0001
                )
            else:
                return RoutingDecision(
                    model=primary['id'],
                    alias=primary['alias'],
                    reason="用户强制指定主模型",
                    confidence=1.0,
                    estimated_cost=0.001
                )
        
        analysis = self.analyze_task(query, context_length)
        
        # 轻量模式触发条件
        if analysis['is_greeting']:
            return RoutingDecision(
                model=lightweight['id'],
                alias=lightweight['alias'],
                reason="问候语 → 轻量模式",
                confidence=0.95,
                estimated_cost=0.00005
            )
        
        if analysis['is_system_check']:
            return RoutingDecision(
                model=lightweight['id'],
                alias=lightweight['alias'],
                reason="系统检查 → 轻量模式 (快速响应)",
                confidence=0.95,
                estimated_cost=0.00005
            )
        
        if analysis['is_short'] and not analysis['is_code_related'] and context_length < 2000:
            return RoutingDecision(
                model=lightweight['id'],
                alias=lightweight['alias'],
                reason="短查询+低上下文 → 轻量模式",
                confidence=0.8,
                estimated_cost=0.0001
            )
        
        # 深度模式触发条件
        if analysis['is_code_related']:
            return RoutingDecision(
                model=primary['id'],
                alias=primary['alias'],
                reason="代码相关 → 深度模式 (Kimi更擅长)",
                confidence=0.95,
                estimated_cost=0.005
            )
        
        if analysis['is_analysis']:
            return RoutingDecision(
                model=primary['id'],
                alias=primary['alias'],
                reason="分析任务 → 深度模式",
                confidence=0.9,
                estimated_cost=0.003
            )
        
        if context_length > 10000:
            return RoutingDecision(
                model=primary['id'],
                alias=primary['alias'],
                reason=f"长上下文 ({context_length} tokens) → 深度模式",
                confidence=0.9,
                estimated_cost=0.005
            )
        
        if analysis['has_complex_reasoning']:
            return RoutingDecision(
                model=primary['id'],
                alias=primary['alias'],
                reason="复杂推理 → 深度模式",
                confidence=0.85,
                estimated_cost=0.003
            )
        
        # 默认使用轻量模式 (成本优化)
        return RoutingDecision(
            model=lightweight['id'],
            alias=lightweight['alias'],
            reason="默认 → 轻量模式 (成本优化)",
            confidence=0.6,
            estimated_cost=0.0005
        )
    
    def print_routing_table(self):
        """打印路由规则表"""
        print("=" * 60)
        print("🔄 双模型智能路由规则")
        print("=" * 60)
        print("\n📊 模型对比:")
        print("  Kimi K2.5 (主模型)")
        print("    - 上下文: 262K tokens")
        print("    - 强项: 代码、推理、长文档")
        print("    - 成本: 较高")
        print()
        print("  Nemotron-Nano (轻量模型)")
        print("    - 上下文: 128K tokens")
        print("    - 强项: 快速响应、简单问答")
        print("    - 成本: 极低 (1/10)")
        
        print("\n📋 路由规则:")
        print("  → 轻量模式 (Nemotron-Nano):")
        print("    • 问候语: 你好/Hi/在吗")
        print("    • 系统检查: HEARTBEAT/状态")
        print("    • 短查询: <50字符 + 低上下文")
        print()
        print("  → 深度模式 (Kimi K2.5):")
        print("    • 代码相关: 编写/生成代码")
        print("    • 分析任务: 深度/详细/架构")
        print("    • 长上下文: >10K tokens")
        print("    • 复杂推理: 为什么/如何解释")
        print("=" * 60)

def main():
    """CLI 入口"""
    router = ModelRouter()
    
    if len(sys.argv) < 2:
        router.print_routing_table()
        print("\n用法: python3 model-router.py '<查询内容>' [--force-primary|--force-lightweight]")
        sys.exit(0)
    
    query = sys.argv[1]
    force = None
    if '--force-lightweight' in sys.argv or '--force-nano' in sys.argv:
        force = 'lightweight'
    elif '--force-primary' in sys.argv or '--force-kimi' in sys.argv:
        force = 'primary'
    
    # 模拟上下文长度 (实际应用中从会话获取)
    context_length = 5000  # 默认值
    
    decision = router.route(query, context_length, force)
    
    print(f"📝 查询: {query[:50]}...")
    print(f"🎯 选择模型: {decision.alias}")
    print(f"💡 理由: {decision.reason}")
    print(f"📊 置信度: {decision.confidence:.0%}")
    print(f"💰 预估成本: ${decision.estimated_cost:.4f}")

if __name__ == '__main__':
    main()
