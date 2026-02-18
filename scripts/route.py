#!/usr/bin/env python3
# 简洁智能路由 v1.0
# 用途：根据任务类型自动选择模型和thinking模式

import re
from typing import Dict, Optional

# ============ 模型定义 ============
MODELS = {
    "step": {
        "full": "nvidia-build/stepfun-ai/step-3.5-flash",
        "name": "step",
        "cost": "免费",
        "speed": "最快",
    },
    "glm": {
        "full": "nvidia-build/z-ai/glm4.7",
        "name": "glm",
        "cost": "免费",
        "speed": "快",
    },
    "kimi": {
        "full": "nvidia-build/moonshotai/kimi-k2.5",
        "name": "kimi",
        "cost": "免费",
        "speed": "中",
    },
    "k2p5": {
        "full": "kimi-coding/k2p5",
        "name": "k2p5",
        "cost": "付费",
        "speed": "中",
    },
}

# ============ 路由规则（核心） ============
ROUTE_RULES = {
    # 生产任务 - step（免费且最快）
    "heartbeat": {"model": "step", "thinking": "off"},
    "monitor": {"model": "step", "thinking": "off"},
    "unified-monitor": {"model": "step", "thinking": "off"},
    "maintenance": {"model": "step", "thinking": "off"},
    "snapshot": {"model": "step", "thinking": "off"},
    "backup": {"model": "step", "thinking": "off"},
    "archive": {"model": "step", "thinking": "off"},

    # 中文任务 - glm（中文优化）
    "chinese": {"model": "glm", "thinking": "on"},
    "translate": {"model": "glm", "thinking": "on"},

    # 文档分析 - kimi（256k上下文）
    "document": {"model": "kimi", "thinking": "on"},
    "scan": {"model": "kimi", "thinking": "on"},
    "moltbook": {"model": "kimi", "thinking": "on"},
    "hn": {"model": "kimi", "thinking": "on"},
    "github": {"model": "kimi", "thinking": "on"},

    # 深度任务 - k2p5（唯一付费场景）
    "deep": {"model": "k2p5", "thinking": "stream"},
    "code": {"model": "k2p5", "thinking": "on"},
    "architecture": {"model": "k2p5", "thinking": "stream"},
}

# ============ 回退链 ============
FALLBACK_CHAIN = ["step", "glm", "kimi", "k2p5"]

# ============ 主路由函数 ============

def route(task_type: str, signal: Optional[int] = None) -> Dict:
    """
    根据任务类型和Signal评分路由

    Args:
        task_type: 任务类型（如 "monitor", "scan", "deep"）
        signal: Signal评分（1-10，可选）

    Returns:
        {
            "model": "step",
            "full_model": "nvidia-build/...",
            "thinking": "off",
            "reason": "简单检查，快速完成"
        }
    """
    # Signal≥9 强制使用 k2p5
    if signal is not None and signal >= 9:
        return {
            "model": "k2p5",
            "full_model": MODELS["k2p5"]["full"],
            "thinking": "stream",
            "reason": "Signal≥9高价值内容，使用最强模型",
        }

    # 查询路由规则（模糊匹配）
    route = _find_route(task_type)

    if route:
        return {
            "model": route["model"],
            "full_model": MODELS[route["model"]]["full"],
            "thinking": route["thinking"],
            "reason": f"任务类型: {task_type}",
        }

    # 默认使用 step
    return {
        "model": "step",
        "full_model": MODELS["step"]["full"],
        "thinking": "off",
        "reason": "未知任务类型，使用默认模型 step",
    }

def _find_route(task_type: str) -> Optional[Dict]:
    """模糊匹配路由规则"""
    # 完全匹配
    if task_type in ROUTE_RULES:
        return ROUTE_RULES[task_type]

    # 前缀匹配（如 "moltbook-scan" → "moltbook"）
    for key, value in ROUTE_RULES.items():
        if task_type.startswith(key):
            return value

    # 关键词匹配
    if any(k in task_type for k in ["chinese", "翻译", "中文"]):
        return ROUTE_RULES["chinese"]
    if any(k in task_type for k in ["scan", "moltbook", "hn"]):
        return ROUTE_RULES["scan"]
    if any(k in task_type for k in ["deep", "架构", "architecture"]):
        return ROUTE_RULES["deep"]

    return None

def fallback_on_failure(current_model: str, attempts: int = 1) -> Dict:
    """
    当前模型失败时返回回退模型

    Args:
        current_model: 当前失败的模型
        attempts: 失败次数

    Returns:
        下一个模型的配置
    """
    idx = FALLBACK_CHAIN.index(current_model) if current_model in FALLBACK_CHAIN else -1

    if idx < len(FALLBACK_CHAIN) - 1:
        next_model = FALLBACK_CHAIN[idx + 1]
        return {
            "model": next_model,
            "full_model": MODELS[next_model]["full"],
            "thinking": "off",
            "reason": f"回退: {current_model} 失败第 {attempts} 次",
        }

    # 已经是最后一个模型，保持
    return {
        "model": current_model,
        "full_model": MODELS[current_model]["full"],
        "thinking": "off",
        "reason": "已是最后一个模型，无法回退",
    }

# ============ 命令行接口 ============

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 route.py <task_type> [signal]")
        print("示例:")
        print("  python3 route.py unified-monitor")
        print("  python3 route.py moltbook-scan")
        print("  python3 route.py deep-learning 9")
        sys.exit(1)

    task = sys.argv[1]
    signal = int(sys.argv[2]) if len(sys.argv) > 2 else None

    result = route(task, signal)

    print("=" * 50)
    print("智能路由结果")
    print("=" * 50)
    print(f"任务类型: {task}")
    if signal:
        print(f"Signal评分: {signal}")
    print(f"建议模型: {result['model']}")
    print(f"完整路径: {result['full_model']}")
    print(f"Thinking: {result['thinking']}")
    print(f"原因: {result['reason']}")
    print("=" * 50)

    # 可选：输出 spawn 命令
    print("\nOpenClaw Spawn命令:")
    print(f"openclaw sessions spawn \\")
    print(f"  --task=\"<实际任务>\" \\")
    print(f"  --agent=main \\")
    print(f"  --model={result['full_model']} \\")
    print(f"  --thinking={result['thinking']}")
