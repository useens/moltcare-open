#!/bin/bash
echo "修复所有配置文件..."

API_KEYS=(
    "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"
    "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"
    "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"
    "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"
    "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"
    "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"
    "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"
    "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"
    "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"
    "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"
)

for i in {1..10}; do
    idx=$((i-1))
    CONFIG_FILE="/root/.openclaw/workspace/nanobot-instances/nanobot-$i/.nanobot/config.json"
    
    cat > "$CONFIG_FILE" <> EOF
{
  "providers": {
    "custom": {
      "api_key": "${API_KEYS[$idx]}",
      "api_base": "https://integrate.api.nvidia.com/v1"
    }
  },
  "agents": {
    "defaults": {
      "model": "stepfun-ai/step-3.5-flash",
      "provider": "custom"
    }
  }
}
EOF
    
    echo "✅ nanobot-$i"
done

echo ""
echo "启动nanobot-1..."
export HOME=/root/.openclaw/workspace/nanobot-instances/nanobot-1
cd /root/.openclaw/workspace/nanobot-instances/nanobot-1
/root/.openclaw/workspace/nanobot-env/bin/nanobot gateway -p 18801 > /tmp/nb1.log 2>&1 &
sleep 5
ps aux | grep nanobot-gateway | grep -v grep