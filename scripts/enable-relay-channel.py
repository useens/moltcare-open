#!/usr/bin/env python3
"""更新所有nanobot配置启用Relay Channel"""

import json
from pathlib import Path

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

for i in range(1, 11):
    nb_id = f"nanobot-{i}"
    config_dir = Path(f"/root/.openclaw/workspace/nanobot-instances/{nb_id}/.nanobot")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        "providers": {
            "custom": {
                "api_key": API_KEYS[i-1],
                "api_base": "https://integrate.api.nvidia.com/v1"
            }
        },
        "agents": {
            "defaults": {
                "model": "stepfun-ai/step-3.5-flash",
                "provider": "custom"
            }
        },
        "channels": {
            "relay": {
                "enabled": True,
                "relay_url": "http://127.0.0.1:19000",
                "bot_id": nb_id,
                "poll_interval": 3,
                "allow_from": ["*"]
            }
        },
        "tools": {
            "restrictToWorkspace": True
        }
    }
    
    config_file = config_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ {nb_id} - Relay channel enabled")

print("\n========================================")
print("✅ 所有10个nanobot配置已更新！")
print("========================================")
print("\n启动命令：")
print("  bash /root/.openclaw/workspace/scripts/start-relay-nanobots.sh")
