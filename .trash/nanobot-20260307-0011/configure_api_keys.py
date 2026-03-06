#!/usr/bin/env python3
"""
为10个Nanobot配置独立的API Key和模型
"""
import json
from pathlib import Path

BASE_DIR = Path("/root/.openclaw/workspace/projects/nanobot/agents")

# 10个API Key (每个nanobot一个)
API_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]

# 模型配置
MODELS = {
    "stepfun-ai/step-3.5-flash": "Step 3.5 Flash",
    "deepseek-ai/deepseek-v3.2": "DeepSeek V3.2",
    "z-ai/glm4.7": "GLM 4.7",
    "moonshotai/kimi-k2.5": "Kimi K2.5"
}

# 为每个nanobot配置
for i in range(1, 11):
    agent_id = f"nanobot-{i}"
    agent_dir = BASE_DIR / agent_id
    
    # 写入.env配置
    env_content = f"""# Nanobot AI Agent Configuration
NVIDIA_API_KEY={API_KEYS[i-1]}
BASE_URL=https://integrate.api.nvidia.com/v1
PROVIDER=nvidia-build
API_TYPE=openai-completions

# 可用模型 (按优先级排序)
MODEL_PRIORITY_1=stepfun-ai/step-3.5-flash
MODEL_PRIORITY_2=deepseek-ai/deepseek-v3.2
MODEL_PRIORITY_3=z-ai/glm4.7
MODEL_PRIORITY_4=moonshotai/kimi-k2.5
"""
    
    with open(agent_dir / ".env", "w") as f:
        f.write(env_content)
    
    print(f"✅ 配置 {agent_id} - API Key: {API_KEYS[i-1][:20]}...")

print()
print("🎉 10个Nanobot API配置完成！")
print("   每个Agent都有独立的API Key")
print("   可用模型: Step 3.5 Flash, DeepSeek V3.2, GLM 4.7, Kimi K2.5")
