#!/bin/bash
echo "修复配置..."
for i in {1..10}; do
    NB_DIR="/root/.openclaw/workspace/nanobot-instances/nanobot-$i"
    mkdir -p "$NB_DIR/.nanobot"
    cp "$NB_DIR/config.json" "$NB_DIR/.nanobot/"
    echo "nanobot-$i OK"
done

echo ""
echo "启动nanobot-1..."
cd /root/.openclaw/workspace/nanobot-instances/nanobot-1
export HOME=/root/.openclaw/workspace/nanobot-instances/nanobot-1
/root/.openclaw/workspace/nanobot-env/bin/nanobot gateway -p 18801 > nanobot.log 2>&1 &
sleep 3
ps aux | grep nanobot-gateway | grep -v grep