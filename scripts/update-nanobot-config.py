#!/usr/bin/env python3
"""
更新10个nanobot的NVIDIA配置
每个nanobot分配独立的API Key
"""

from pathlib import Path
import json

# 10个独立的API Key
API_KEYS = [
    "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",  # nanobot-1
    "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",  # nanobot-2
    "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",  # nanobot-3
    "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",  # nanobot-4
    "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",  # nanobot-5
    "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",  # nanobot-6
    "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",  # nanobot-7
    "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",  # nanobot-8
    "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",  # nanobot-9
    "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",  # nanobot-10
]

# 模型分配
MODEL_ASSIGNMENTS = {
    "nanobot-1": {"model": "stepfun-ai/step-3.5-flash", "name": "Step 3.5 Flash"},
    "nanobot-2": {"model": "stepfun-ai/step-3.5-flash", "name": "Step 3.5 Flash"},
    "nanobot-3": {"model": "deepseek-ai/deepseek-v3.2", "name": "DeepSeek V3.2"},
    "nanobot-4": {"model": "stepfun-ai/step-3.5-flash", "name": "Step 3.5 Flash"},
    "nanobot-5": {"model": "stepfun-ai/step-3.5-flash", "name": "Step 3.5 Flash"},
    "nanobot-6": {"model": "deepseek-ai/deepseek-v3.2", "name": "DeepSeek V3.2"},
    "nanobot-7": {"model": "deepseek-ai/deepseek-v3.2", "name": "DeepSeek V3.2"},
    "nanobot-8": {"model": "deepseek-ai/deepseek-v3.2", "name": "DeepSeek V3.2"},
    "nanobot-9": {"model": "z-ai/glm4.7", "name": "GLM 4.7"},
    "nanobot-10": {"model": "moonshotai/kimi-k2.5", "name": "Kimi K2.5"},
}

BASE_CONFIG = {
    "provider": "nvidia-build",
    "base_url": "https://integrate.api.nvidia.com/v1",
    "api": "openai-completions"
}

def update_nanobot_config(nb_id: str, api_key: str):
    """更新单个nanobot的配置"""
    nb_dir = Path(f"/root/.openclaw/workspace/ai-nanobots/{nb_id}")
    
    # 更新identity.json
    identity_file = nb_dir / "identity.json"
    if identity_file.exists():
        with open(identity_file) as f:
            identity = json.load(f)
        
        identity["api_key"] = api_key
        identity["provider"] = BASE_CONFIG["provider"]
        identity["base_url"] = BASE_CONFIG["base_url"]
        identity["api"] = BASE_CONFIG["api"]
        
        # 更新模型
        model_info = MODEL_ASSIGNMENTS.get(nb_id, {})
        identity["model"] = model_info.get("model", "stepfun-ai/step-3.5-flash")
        identity["model_name"] = model_info.get("name", "Step 3.5 Flash")
        
        with open(identity_file, "w") as f:
            json.dump(identity, f, indent=2, ensure_ascii=False)
    
    # 创建.env文件
    env_file = nb_dir / ".env"
    env_content = f"""NVIDIA_API_KEY={api_key}
PROVIDER={BASE_CONFIG['provider']}
BASE_URL={BASE_CONFIG['base_url']}
API={BASE_CONFIG['api']}
MODEL={MODEL_ASSIGNMENTS.get(nb_id, {}).get('model', 'stepfun-ai/step-3.5-flash')}
"""
    env_file.write_text(env_content)
    
    print(f"✅ {nb_id} 配置已更新")
    print(f"   模型: {MODEL_ASSIGNMENTS.get(nb_id, {}).get('name', 'Step 3.5 Flash')}")
    print(f"   API Key: {api_key[:20]}...")

def main():
    print("=" * 70)
    print("更新10个nanobot的NVIDIA配置")
    print("=" * 70)
    print()
    
    for i in range(1, 11):
        nb_id = f"nanobot-{i}"
        api_key = API_KEYS[i-1]
        update_nanobot_config(nb_id, api_key)
        print()
    
    print("=" * 70)
    print("✅ 所有nanobot配置已更新！")
    print("=" * 70)
    print()
    print("模型分配:")
    for i in range(1, 11):
        nb_id = f"nanobot-{i}"
        model = MODEL_ASSIGNMENTS.get(nb_id, {}).get("name", "Step 3.5 Flash")
        print(f"  {nb_id}: {model}")

if __name__ == "__main__":
    main()
