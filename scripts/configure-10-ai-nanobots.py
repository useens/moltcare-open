#!/usr/bin/env python3
"""
配置真正的10个AI nanobot
基于现有的nanobot.py创建9个副本，配置不同模型
删除10个空壳node-{1-10}
"""

import os
import shutil
from pathlib import Path

# 源nanobot
SOURCE_PATH = Path("/root/.openclaw/workspace/nanobot")

# 目标目录
AI_NANOBOTS_BASE = Path("/root/.openclaw/workspace/ai-nanobots")

# 模型配置
MODEL_CONFIGS = {
    "nanobot-1": {
        "model": "step-3.5-flash",
        "provider": "nvidia",
        "model_id": "stepfun-ai/step-3.5-flash",
        "role": "fast_executor",
        "name": "快速执行者",
        "description": "快速响应，处理简单任务"
    },
    "nanobot-2": {
        "model": "step-3.5-flash",
        "provider": "nvidia",
        "model_id": "stepfun-ai/step-3.5-flash",
        "role": "data_collector",
        "name": "数据收集者",
        "description": "网络爬取，数据采集"
    },
    "nanobot-3": {
        "model": "step-3.5-flash",
        "provider": "nvidia",
        "model_id": "stepfun-ai/step-3.5-flash",
        "role": "content_generator",
        "name": "内容生成者",
        "description": "文本生成，内容创作"
    },
    "nanobot-4": {
        "model": "step-3.5-flash",
        "provider": "nvidia",
        "model_id": "stepfun-ai/step-3.5-flash",
        "role": "api_caller",
        "name": "API调用者",
        "description": "API调用，服务集成"
    },
    "nanobot-5": {
        "model": "step-3.5-flash",
        "provider": "nvidia",
        "model_id": "stepfun-ai/step-3.5-flash",
        "role": "monitor",
        "name": "监控者",
        "description": "系统监控，状态检测"
    },
    "nanobot-6": {
        "model": "deepseek-v3.2",
        "provider": "deepseek",
        "model_id": "deepseek-ai/deepseek-v3.2",
        "role": "deep_analyzer",
        "name": "深度分析者",
        "description": "深度分析，复杂推理"
    },
    "nanobot-7": {
        "model": "deepseek-v3.2",
        "provider": "deepseek",
        "model_id": "deepseek-ai/deepseek-v3.2",
        "role": "code_reviewer",
        "name": "代码审查者",
        "description": "代码审查，质量检查"
    },
    "nanobot-8": {
        "model": "deepseek-v3.2",
        "provider": "deepseek",
        "model_id": "deepseek-ai/deepseek-v3.2",
        "role": "complex_solver",
        "name": "复杂解决者",
        "description": "复杂问题，算法设计"
    },
    "nanobot-9": {
        "model": "deepseek-v3.2",
        "provider": "deepseek",
        "model_id": "deepseek-ai/deepseek-v3.2",
        "role": "strategy_planner",
        "name": "策略规划者",
        "description": "策略规划，架构设计"
    },
    "nanobot-10": {
        "model": "deepseek-v3.2",
        "provider": "deepseek",
        "model_id": "deepseek-ai/deepseek-v3.2",
        "role": "quality_assurance",
        "name": "质量保证者",
        "description": "质量保证，测试验证"
    },
}

def create_nanobot(nb_id: str, config: dict):
    """创建单个nanobot实例"""
    target_dir = AI_NANOBOTS_BASE / nb_id
    target_dir.mkdir(parents=True, exist_ok=True)

    # 复制源文件
    for file in ["nanobot.py", "nanobot_ai.py", "nanobot.service"]:
        src = SOURCE_PATH / file
        dst = target_dir / file
        if src.exists():
            shutil.copy2(src, dst)

    # 修改nanobot.py中的配置
    nanobot_py = target_dir / "nanobot.py"
    if nanobot_py.exists():
        content = nanobot_py.read_text()

        # 修改节点ID
        content = content.replace(
            'NANOBOT_DIR = Path("/root/.openclaw/workspace/nanobot")',
            f'NANOBOT_DIR = Path("/root/.openclaw/workspace/ai-nanobots/{nb_id}")'
        )

        # 修改LOG_FILE
        content = content.replace(
            'LOG_FILE = NANOBOT_DIR / "nanobot.log"',
            f'LOG_FILE = NANOBOT_DIR / "{nb_id}.log"'
        )

        # 修改SESSION_FILE
        content = content.replace(
            'SESSION_FILE = NANOBOT_DIR / "session.json"',
            f'SESSION_FILE = NANOBOT_DIR / "session.json"'
        )

        # 修改名称
        content = content.replace(
                'self.name = "虾米派派 (Nanobot)"',
                f'self.name = "{config["name"]} ({nb_id})"'
        )

        # 修改版本
        content = content.replace(
                'self.version = "2.3"',
                f'self.version = "3.0"'
        )

        nanobot_py.write_text(content)

    # 修改nanobot_ai.py中的模型配置
    nanobot_ai_py = target_dir / "nanobot_ai.py"
    if nanobot_ai_py.exists():
        content = nanobot_ai_py.read_text()

        if config["provider"] == "nvidia":
            content = content.replace(
                '"stepfun-ai/step-3.5-flash"',
                f'"{config["model_id"]}"'
            )
            content = content.replace(
                '"name": "step-3.5-flash"',
                f'"name": "{config["model"]}"'
            )
        elif config["provider"] == "deepseek":
            content = content.replace(
                '"name": "step-3.5-flash"',
                f'"name": "{config["model"]}"'
            )
            content = content.replace(
                '"stepfun-ai/step-3.5-flash"',
                f'"{config["model_id"]}"'
            )
            # 需要修改base_url为DeepSeek
            content = content.replace(
                '"base_url": "https://integrate.api.nvidia.com/v1"',
                '"base_url": "https://api.deepseek.com/v1"'
            )

        nanobot_ai_py.write_text(content)

    # 创建身份文件
    identity_file = target_dir / "identity.json"
    identity = {
        "id": nb_id,
        "name": config["name"],
        "role": config["role"],
        "description": config["description"],
        "model": config["model"],
        "provider": config["provider"],
        "model_id": config["model_id"]
    }
    import json
    with open(identity_file, "w") as f:
        json.dump(identity, f, indent=2, ensure_ascii=False)

    print(f"✅ 创建 {nb_id} - {config['name']} ({config['model']})")

def delete_shell_nodes():
    """删除10个空壳节点"""
    print("\n" + "=" * 70)
    print("删除10个空壳节点...")
    print("=" * 70)

    cluster_dir = Path("/root/.openclaw/workspace/nanobot-cluster")
    if cluster_dir.exists():
        for i in range(1, 11):
            node_dir = cluster_dir / f"node-{i}"
            if node_dir.exists():
                print(f"🗑️  删除 {node_dir}")
                shutil.rmtree(node_dir)

def main():
    """主函数"""
    print("=" * 70)
    print("配置10个真正的AI nanobot")
    print("=" * 70)
    print()

    # 创建AI nanobots
    for nb_id, config in MODEL_CONFIGS.items():
        create_nanobot(nb_id, config)

    # 删除空壳节点
    delete_shell_nodes()

    print("\n" + "=" * 70)
    print("✅ 配置完成！10个AI nanobot已创建")
    print("=" * 70)
    print()
    print("下一步：启动所有nanobot")
    print("  cd /root/.openclaw/workspace/scripts")
    print("  bash start-10-ai-nanobots.sh")
    print("=" * 70)

if __name__ == "__main__":
    main()
