#!/usr/bin/env python3
"""更新nanobot-6到nanobot-10为Step 3.5 Flash"""

from pathlib import Path
import json

for i in range(6, 11):
    nb_id = f"nanobot-{i}"
    nb_dir = Path(f"/root/.openclaw/workspace/ai-nanobots/{nb_id}")
    
    # 读取现有API Key
    env_file = nb_dir / ".env"
    api_key = ""
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("NVIDIA_API_KEY="):
                    api_key = line.strip().split("=", 1)[1]
                    break
    
    # 如果没有，使用对应的key
    if not api_key:
        api_keys = {
            6: "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",
            7: "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",
            8: "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",
            9: "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",
            10: "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"
        }
        api_key = api_keys.get(i, "")
    
    # 更新.env
    env_content = f"""NVIDIA_API_KEY={api_key}
PROVIDER=nvidia-build
BASE_URL=https://integrate.api.nvidia.com/v1
API=openai-completions
MODEL=stepfun-ai/step-3.5-flash
"""
    with open(env_file, "w") as f:
        f.write(env_content)
    
    # 更新identity.json
    identity_file = nb_dir / "identity.json"
    if identity_file.exists():
        with open(identity_file) as f:
            identity = json.load(f)
        identity["model"] = "stepfun-ai/step-3.5-flash"
        identity["model_name"] = "Step 3.5 Flash"
        with open(identity_file, "w") as f:
            json.dump(identity, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {nb_id} 已更新为 Step 3.5 Flash")

print("\n重启所有nanobot...")
