#!/bin/bash
# 神经中枢 2.0 完整部署脚本

set -e

cd /root/.openclaw/workspace

echo "=" * 60
echo "🚀 神经中枢 2.0 部署"
echo "=" * 60

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -q redis 2>/dev/null || true

# 创建数据目录
mkdir -p data/neural_hub/logs
mkdir -p data/neural_hub/sockets

echo ""
echo "✅ 依赖安装完成"

# 部署选项
echo ""
echo "选择部署模式:"
echo "1) 快速测试 (仅启动核心)"
echo "2) 完整部署 (核心 + 10个nanobot)"
echo "3) 安装Systemd服务"
read -p "选择 [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "🧠 启动神经中枢核心..."
        python3 scripts/start-neural-hub.py
        ;;
    
    2)
        echo ""
        echo "🧠 启动神经中枢核心 (后台)..."
        nohup python3 scripts/start-neural-hub.py > data/neural_hub/logs/hub.log 2>&1 &
echo $! > data/neural_hub/hub.pid
        sleep 2
        
        echo "🤖 启动10个Nanobot V3..."
        ./ai-nanobots/start-all-v3.sh
        
        echo ""
        echo "✅ 完整部署完成！"
        echo ""
        echo "查看状态:"
        echo "  - 神经中枢: tail -f data/neural_hub/logs/hub.log"
        echo "  - Nanobot:  tail -f data/neural_hub/logs/nanobot-*.log"
        echo ""
        echo "停止所有: ./scripts/stop-neural-hub.sh"
        ;;
    
    3)
        echo ""
        echo "📦 安装Systemd服务..."
        
        cp config/neural-hub.service /etc/systemd/system/
        cp config/nanobot-v3@.service /etc/systemd/system/
        
        systemctl daemon-reload
        
        echo "✅ 服务文件已安装"
        echo ""
        echo "使用方法:"
        echo "  systemctl start neural-hub      # 启动神经中枢"
        echo "  systemctl start nanobot-v3@1    # 启动nanobot-1"
        echo "  systemctl start nanobot-v3@{1..10}  # 启动全部10个"
        echo ""
        ;;
    
    *)
        echo "无效选择"
        exit 1
        ;;
esac
