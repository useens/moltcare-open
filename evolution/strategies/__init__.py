"""
所有进化策略的统一注册中心
"""

from typing import Dict, Any, Optional

# 导入各维度策略模块
from evolution.strategies.cognitive import STRATEGIES as COGNITIVE_STRATEGIES
from evolution.strategies.learning import LEARNING_STRATEGIES, get_strategy as get_learning_strategy
from evolution.strategies.autonomy import AUTONOMY_STRATEGIES, get_strategy as get_autonomy_strategy
from evolution.strategies.goal import GOAL_STRATEGIES, get_strategy as get_goal_strategy
from evolution.strategies.creativity import CREATIVITY_STRATEGIES, get_strategy as get_creativity_strategy
from evolution.strategies.adaptive import ADAPTIVE_STRATEGIES, get_strategy as get_adaptive_strategy
from evolution.strategies.collaboration import COLLABORATION_STRATEGIES, get_strategy as get_collaboration_strategy
from evolution.strategies.protection import PROTECTION_STRATEGIES, get_strategy as get_protection_strategy
from evolution.strategies.prediction import PREDICTION_STRATEGIES, get_strategy as get_prediction_strategy
from evolution.strategies.self_awareness import SELF_AWARENESS_STRATEGIES, get_strategy as get_self_awareness_strategy

# 统一策略字典
ALL_STRATEGIES: Dict[str, Dict] = {
    "cognitive": COGNITIVE_STRATEGIES,
    "learning": LEARNING_STRATEGIES,
    "autonomy": AUTONOMY_STRATEGIES,
    "goal": GOAL_STRATEGIES,
    "creativity": CREATIVITY_STRATEGIES,
    "adaptive": ADAPTIVE_STRATEGIES,
    "collaboration": COLLABORATION_STRATEGIES,
    "protection": PROTECTION_STRATEGIES,
    "prediction": PREDICTION_STRATEGIES,
    "self_awareness": SELF_AWARENESS_STRATEGIES
}

# 维度策略获取器（cognitive维度需要特殊处理）
def get_cognitive_strategy(name: str):
    """获取认知维度策略"""
    return COGNITIVE_STRATEGIES.get(name)

DIMENSION_GETTERS = {
    "cognitive": get_cognitive_strategy,
    "learning": get_learning_strategy,
    "autonomy": get_autonomy_strategy,
    "goal": get_goal_strategy,
    "creativity": get_creativity_strategy,
    "adaptive": get_adaptive_strategy,
    "collaboration": get_collaboration_strategy,
    "protection": get_protection_strategy,
    "prediction": get_prediction_strategy,
    "self_awareness": get_self_awareness_strategy
}

def get_strategy(dim_id: str, strategy_name: str) -> Optional[Any]:
    """获取指定维度的策略实例"""
    getter = DIMENSION_GETTERS.get(dim_id)
    if getter:
        return getter(strategy_name)
    return None

def list_all_strategies() -> Dict[str, Dict]:
    """列出所有可用策略"""
    result = {}
    for dim_id, strategies in ALL_STRATEGIES.items():
        result[dim_id] = list(strategies.keys())
    return result

def total_strategy_count() -> int:
    """返回策略总数"""
    return sum(len(strategies) for strategies in ALL_STRATEGIES.values())

if __name__ == "__main__":
    print("=" * 60)
    print("超进化引擎 v3.0 - 策略注册中心")
    print("=" * 60)
    
    print("\n✅ 维度策略概览:\n")
    for dim_id, strategies in ALL_STRATEGIES.items():
        print(f"  📦 {dim_id}: {len(strategies)} 个策略")
        for name in strategies:
            print(f"     - {name}")
    
    total = total_strategy_count()
    print(f"\n📊 总策略数: {total}/40")
    print("=" * 60)
