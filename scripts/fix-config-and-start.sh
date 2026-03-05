#!/bin/bash
echo "修复配置文件格式..."

for i in {1..10}; do
    CONFIG_FILE="/root/.openclaw/workspace/nanobot-instances/nanobot-$i/.nanobot/config.json"
    
    # 使用正确的字段名 api_key 和 api_base
    cat > "$CONFIG_FILE" << 'EOF'
{
  "providers": {
    "custom": {
      "api_key": "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",
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
    
    echo "✅ nanobot-$i 配置已修复"
done

echo ""
echo "启动nanobot-1测试..."
export HOME=/root/.openclaw/workspace/nanobot-instances/nanobot-1
cd /root/.openclaw/workspace/nanobot-instances/nanobot-1
/root/.openclaw/workspace/nanobot-env/bin/nanobot gateway -p 18801 &
sleep 5
ps aux | grep nanobot-gateway | grep -v grep