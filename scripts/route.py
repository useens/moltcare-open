#!/usr/bin/env python3
# 简洁智能路由 v1.0
# 用途：根据任务类型自动选择模型和thinking模式

import re
from typing import Dict, Optional

# ============ 模型定义 ============
# 2026-02-18 更新：根据 OpenClaw 需求优化模型选择
MODELS = {
    "glm": {
        "full": "nvidia-build/z-ai/glm4.7",
        "name": "glm",
        "cost": "免费",
        "speed": "快",
        "strength": "⭐ 主模型 - 工具调用 + JSON 格式化 + 中文",
    },
    "step": {
        "full": "nvidia-build/stepfun-ai/step-3.5-flash",
        "name": "step",
        "cost": "免费",
        "speed": "最快",
        "strength": "⚡ 快速响应 - 简单检查任务",
    },
    "kimi": {
        "full": "nvidia-build/moonshotai/kimi-k2.5",
        "name": "kimi",
        "cost": "免费",
        "speed": "中",
        "strength": "📚 大上下文 - 文档扫描（256k）",
    },
    "k2p5": {
        "full": "kimi-coding/k2p5",
        "name": "k2p5",
        "cost": "付费",
        "speed": "中",
        "strength": "💎 最强 - 深度架构 + Signal≥9",
    },
}

# ============ 路由规则（核心） ============
# 2026-02-18 更新：GLM-4.7 更适合 OpenClaw 核心任务（工具调用、JSON 格式化、中文）
ROUTE_RULES = {
    # OpenClaw 核心工具任务 - glm（最佳工具调用 + JSON 格式化稳定性）
    "tool": {"model": "glm", "thinking": "on"},
    "exec": {"model": "glm", "thinking": "on"},
    "write": {"model": "glm", "thinking": "on"},
    "read": {"model": "glm", "thinking": "off"},
    "file": {"model": "glm", "thinking": "on"},
    "feishu": {"model": "glm", "thinking": "on"},
    "bitable": {"model": "glm", "thinking": "on"},
    "wiki": {"model": "glm", "thinking": "on"},

    # 简单检查任务 - step（快速响应）
    "heartbeat": {"model": "step", "thinking": "off"},
    "status": {"model": "step", "thinking": "off"},
    "check": {"model": "step", "thinking": "off"},

    # 需要复杂逻辑的监控任务 - glm（推理深度）
    "monitor": {"model": "glm", "thinking": "on"},
    "unified-monitor": {"model": "glm", "thinking": "on"},
    "daemon": {"model": "glm", "thinking": "on"},

    # 维护任务 - glm（稳定性优先）
    "maintenance": {"model": "glm", "thinking": "on"},
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
    "code": {"model": "glm", "thinking": "on"},  # 代码用 glm 也足够，减少成本
    "architecture": {"model": "k2p5", "thinking": "stream"},
}

# ============ 回退链 ============
# 2026-02-18 更新：GLM-4.7 为主模型，step 为快速备选
FALLBACK_CHAIN = ["glm", "step", "kimi", "k2p5"]

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

    # 默认使用 glm（适合 OpenClaw 工具调用场景）
    return {
        "model": "glm",
        "full_model": MODELS["glm"]["full"],
        "thinking": "on",
        "reason": "未知任务类型，使用默认模型 glm（工具调用优化）",
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
