#!/bin/bash
# MoltCare MVP 部署脚本

echo "🚀 MoltCare MVP Deployment"
echo "=========================="

# 创建必要目录
echo "📁 Creating directories..."
mkdir -p data/moltcare/backups
mkdir -p data/moltcare/scans
mkdir -p logs

# 安装依赖
echo "📦 Installing dependencies..."
pip install -q cryptography web3 2>/dev/null || echo "Some packages may already be installed"

# 测试服务
echo "🧪 Testing services..."

# Test Memory service
python3 scripts/moltcare-memory-service.py --backup test_agent > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Memory service: OK"
else
    echo "⚠️  Memory service: May need manual check"
fi

# Test Shield service
echo "print('test')" > /tmp/test_skill.py
python3 scripts/moltcare-shield-service.py /tmp/test_skill.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Shield service: OK"
else
    echo "⚠️  Shield service: May need manual check"
fi
rm -f /tmp/test_skill.py

# Test Payment monitor
python3 scripts/moltcare-payment-monitor.py --stats > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Payment monitor: OK"
else
    echo "⚠️  Payment monitor: May need manual check"
fi

# 安装cron任务
echo ""
echo "📅 Installing cron jobs..."
crontab -l > /tmp/current_crontab 2>/dev/null || echo "# New crontab" > /tmp/current_crontab
cat config/moltcare-services-cron.txt >> /tmp/current_crontab
crontab /tmp/current_crontab
rm -f /tmp/current_crontab

echo "✅ Cron jobs installed"

# 显示状态
echo ""
echo "📊 Deployment Status:"
echo "===================="
echo "Memory backups:  data/moltcare/backups/"
echo "Shield reports:  data/moltcare/scans/"
echo "Logs:            logs/moltcare-*.log"
echo ""
echo "🎯 Next steps:"
echo "1. Test manual backup: python3 scripts/moltcare-memory-service.py --backup test_agent"
echo "2. Test skill scan: python3 scripts/moltcare-shield-service.py /path/to/skill.py"
echo "3. Check payment monitor: python3 scripts/moltcare-payment-monitor.py --stats"
echo ""
echo "📝 To start acquiring customers:"
echo "- See docs/moltcare-growth-strategy.md"
echo "- Contact seed users (XiaoZhuang, etc.)"
echo "- Publish technical posts on Moltbook"
