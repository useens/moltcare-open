#!/usr/bin/env python3
"""
自动模型路由器
监听新消息，如果检测到自动路由规则匹配，建议切换模型
集成策略：
- 对于子代理，在 spawn 前自动评估
- 对于直接消息，提供建议
"""

import json
import subprocess
import sys
from pathlib import Path

CONFIG_PATH = Path("/root/.openclaw/workspace/config/model-routing.yaml")
ROUTING_RULES_PATH = Path("/root/.openclaw/workspace/config/auto-routing-rules.md")

def load_routing_rules():
    """加载路由规则"""
    # 简单实现：读取 auto-routing-rules.md 作为提示词
    # 实际应该解析 YAML
    if ROUTING_RULES_PATH.exists():
        return ROUTING_RULES_PATH.read_text()
    return ""

def evaluate_task(task_text, current_model):
    """评估任务并返回建议"""
    # 调用 assess-difficulty.py 获取难度
    result = subprocess.run(
        ["python3", "/root/.openclaw/workspace/scripts/assess-difficulty.py", task_text],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None

    lines = result.stdout.strip().split('\n')
    info = {}
    for line in lines:
        if ':' in line:
            key, val = line.split(':', 1)
            info[key.strip()] = val.strip()

    difficulty = int(info.get('难度级别', 'L2')[1:])
    suggested_model = info.get('推荐模型')
    thinking = info.get('Thinking模式')
    reason = info.get('原因')

    # 如果建议模型与当前模型相同，不切换
    if suggested_model == current_model:
        return {
            "action": "none",
            "reason": f"当前模型 {current_model} 已是最优选择（{reason}）"
        }

    return {
        "action": "suggest",
        "current_model": current_model,
        "suggested_model": suggested_model,
        "thinking_mode": thinking,
        "difficulty": f"L{difficulty}",
        "reason": reason,
        "confidence": 85 if difficulty >= 3 else 70
    }

def format_suggestion(suggestion):
    """格式化建议消息"""
    if suggestion["action"] == "none":
        return None

    msg = f"""🔀 **模型路由建议**

当前: `{suggestion['current_model']}`
建议: `{suggestion['suggested_model']}`
难度: {suggestion['difficulty']}
Thinking: {suggestion['thinking_mode']}
原因: {suggestion['reason']}

回复 y 确认切换，n 保持当前。"""

    return msg

def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("Usage: auto-model-router.py <task_text> <current_model> [--suggest-only]")
        sys.exit(1)

    task_text = sys.argv[1]
    current_model = sys.argv[2]
    suggest_only = "--suggest-only" in sys.argv

    suggestion = evaluate_task(task_text, current_model)

    if not suggestion or suggestion["action"] == "none":
        if suggest_only:
            print(json.dumps({"action": "none"}))
        else:
            print(suggestion.get("reason", "无需切换模型"))
        sys.exit(0)

    formatted = format_suggestion(suggestion)

    if suggest_only:
        print(json.dumps(suggestion))
    else:
        print(formatted)

if __name__ == "__main__":
    main()
