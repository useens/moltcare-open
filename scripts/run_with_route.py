#!/usr/bin/env python3
# 智能路由包装器 - Python版
# 用途：Cron任务或子代理自动选择模型

import sys
import os
import subprocess
from pathlib import Path

# 添加scripts到路径
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from route import route, MODELS

def get_current_model_config():
    """
    获取当前启用的模型配置
    优先级：环境变量 > 路由判断 > 默认
    """
    # 检查环境变量
    if "OPENCLAW_MODEL" in os.environ:
        model = os.environ["OPENCLAW_MODEL"]
        # 映射完整路径到简短名称
        for name, config in MODELS.items():
            if config["full"] == model:
                return {
                    "model": name,
                    "full_model": model,
                    "thinking": os.environ.get("OPENCLAW_THINKING", "off"),
                    "source": "env"
                }

    # 默认使用 step
    return {
        "model": "step",
        "full_model": MODELS["step"]["full"],
        "thinking": "off",
        "source": "default"
    }

def print_route_info(task_type: str):
    """打印路由信息"""
    routing = route(task_type)
    print("=" * 60)
    print("🧠 智能路由激活")
    print("=" * 60)
    print(f"任务类型: {task_type}")
    print(f"建议模型: {routing['model']}")
    print(f"完整路径: {routing['full_model']}")
    print(f"Thinking: {routing['thinking']}")
    print(f"原因: {routing['reason']}")
    print("=" * 60)
    print()

    return routing

def spawn_with_route(task: str, task_type: str, agent: str = "main"):
    """
    使用智能路由spawn子代理

    Args:
        task: 实际任务描述
        task_type: 任务类型（用于路由）
        agent: agent ID
    """
    routing = route(task_type)

    cmd = [
        "openclaw", "sessions", "spawn",
        "--task", task,
        "--agent", agent,
        "--model", routing["full_model"],
        "--thinking", routing["thinking"]
    ]

    print("=" * 60)
    print("🚀 Spawn 子代理（智能路由）")
    print("=" * 60)
    print(f"任务: {task}")
    print(f"Agent: {agent}")
    print(f"模型: {routing['model']}")
    print(f"Thinking: {routing['thinking']}")
    print("=" * 60)

    # 执行spawn
    result = subprocess.run(cmd, capture_output=False)

    return result.returncode == 0

# 命令行接口
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  1. 获取路由配置:")
        print("     python3 run_with_route.py <task_type>")
        print("")
        print("  2. Spawn子代理:")
        print("     python3 run_with_route.py spawn \"<任务>\" <task_type>")
        print("")
        print("  3. 获取当前配置:")
        print("     python3 run_with_route.py current")
        print("")
        print("示例:")
        print("  python3 run_with_route.py unified-monitor")
        print('  python3 run_with_route.py spawn "扫描Moltbook" moltbook-scan')
        print("  python3 run_with_route.py current")
        sys.exit(1)

    action = sys.argv[1]

    if action == "current":
        config = get_current_model_config()
        print(f"当前模型: {config['model']}")
        print(f"完整路径: {config['full_model']}")
        print(f"Thinking: {config['thinking']}")
        print(f"来源: {config['source']}")

    elif action == "spawn":
        if len(sys.argv) < 4:
            print("❌ 错误: spawn 需要任务描述和任务类型")
            print("用法: python3 run_with_route.py spawn \"<任务>\" <task_type>")
            sys.exit(1)

        task = sys.argv[2]
        task_type = sys.argv[3]
        agent = sys.argv[4] if len(sys.argv) > 4 else "main"

        spawn_with_route(task, task_type, agent)

    else:
        # 默认：打印路由信息
        task_type = sys.argv[1]
        print_route_info(task_type)
