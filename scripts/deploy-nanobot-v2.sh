#!/bin/bash
# 部署Nanobot v2.0并测试

NANOBOT_DIR=/root/.openclaw/workspace/projects/nanobot

echo "🚀 部署Nanobot v2.0"
echo "==================="
echo ""

# 备份旧版本
echo "1️⃣ 备份旧版本..."
cp $NANOBOT_DIR/agent.py $NANOBOT_DIR/agent_v1_backup.py
echo "  已备份到 agent_v1_backup.py"

# 部署新版本
echo ""
echo "2️⃣ 部署v2.0..."
cp $NANOBOT_DIR/agent_v2.py $NANOBOT_DIR/agent.py
echo "  已部署agent_v2.py → agent.py"

# 停止所有Agent
echo ""
echo "3️⃣ 停止当前Agent进程..."
pkill -f "agent.py nanobot" 2>/dev/null
sleep 2

# 启动新版本
echo ""
echo "4️⃣ 启动v2.0 Agent..."
cd $NANOBOT_DIR
for i in $(seq 1 3); do  # 先启动3个测试
    nohup python3 agent.py nanobot-${i} > logs/nanobot-${i}.log 2>&1 &
echo "  nanobot-${i} 已启动"
    sleep 1
done

sleep 3

echo ""
echo "5️⃣ 检查Agent状态..."
ps aux | grep "agent.py nanobot" | grep -v grep | wc -l
echo "  个Agent运行中"

echo ""
echo "✅ Nanobot v2.0 部署完成"
