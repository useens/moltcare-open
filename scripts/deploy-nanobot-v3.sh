#!/bin/bash
# 部署Nanobot v3.0 自我进化版

echo "🚀 部署Nanobot v3.0 自我进化版"
echo "==============================="
echo ""

NANOBOT_DIR=/root/.openclaw/workspace/projects/nanobot

# 备份当前版本
echo "1️⃣ 备份当前版本..."
cp $NANOBOT_DIR/agent.py $NANOBOT_DIR/agent_v2_backup.py
echo "  ✅ 已备份到 agent_v2_backup.py"

# 部署v3.0
echo ""
echo "2️⃣ 部署v3.0..."
cp $NANOBOT_DIR/agent_v3.py $NANOBOT_DIR/agent.py
echo "  ✅ 已部署agent_v3.py → agent.py"

# 创建自我修改目录
mkdir -p $NANOBOT_DIR/self_modifications/backups
echo "  ✅ 已创建自我修改目录"

# 停止所有Agent
echo ""
echo "3️⃣ 停止当前Agent..."
pkill -f "agent.py nanobot" 2>/dev/null
sleep 2

# 启动v3.0 Agent
echo ""
echo "4️⃣ 启动v3.0 Agent..."
cd $NANOBOT_DIR
for i in 1 2 3; do
    nohup python3 agent.py nanobot-${i} > logs/nanobot-${i}.log 2>&1 &
echo "  nanobot-${i} 已启动"
    sleep 1
done

sleep 3

echo ""
echo "5️⃣ 检查状态..."
ps aux | grep "agent.py nanobot" | grep -v grep | wc -l
echo "  个Agent运行中"

echo ""
echo "✅ Nanobot v3.0 自我进化版部署完成！"
echo ""
echo "💡 v3.0新增功能:"
echo "  - 自我代码修改 (self_modify)"
echo "  - 自动备份机制"
echo "  - 修改回滚能力"
echo "  - 变更历史记录"
