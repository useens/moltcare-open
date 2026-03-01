#!/bin/bash
# Polymarket Monitor 安装脚本

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         📊 Polymarket Monitor 安装向导                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 检查Python版本
echo "🔍 检查Python环境..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python版本: $python_version"

# 创建虚拟环境
echo ""
echo "📦 创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "✓ 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "📥 安装依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建必要的目录
echo ""
echo "📁 创建目录结构..."
mkdir -p logs
mkdir -p data
mkdir -p reports/alerts
mkdir -p scripts

# 创建配置文件
echo ""
echo "⚙️ 创建配置文件..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Polymarket Monitor 配置
CHECK_INTERVAL=300
SPIKE_THRESHOLD=0.30
VOLUME_THRESHOLD=1000
TIME_WINDOW=3600
ALERT_COOLDOWN=3600

# 通知配置 (可选)
# TELEGRAM_BOT_TOKEN=your_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here
# EMAIL_SMTP_HOST=smtp.gmail.com
# EMAIL_SMTP_PORT=587
# EMAIL_USERNAME=your_email@gmail.com
# EMAIL_PASSWORD=your_app_password
EOF
    echo "✓ 配置文件 .env 已创建"
fi

# 设置权限
chmod +x scripts/*.sh 2>/dev/null
chmod +x monitor.py

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用方法:"
echo "  1. 激活虚拟环境: source venv/bin/activate"
echo "  2. 启动监控: python monitor.py"
echo "  3. 查看报告: cat reports/daily_report.md"
echo ""
echo "提示: 根据您的需求编辑 .env 文件来调整配置参数"
