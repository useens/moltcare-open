#!/bin/bash
# Moltbook API 社交自动化 - 启动脚本

echo "🚀 Moltbook API 社交自动化"
echo "================================"
echo ""

# 检查凭证
if [ ! -f /root/.config/moltbook/credentials.json ]; then
    echo "❌ 错误: 凭证文件不存在"
    exit 1
fi

# 运行API自动化
echo "🤖 启动 API 社交自动化..."
python3 /root/.openclaw/workspace/scripts/moltbook-api-automation.py

echo ""
echo "📊 查看日志:"
echo "  tail -50 /root/.openclaw/workspace/data/moltbook/api-automation.log"
echo ""
echo "📈 查看状态:"
echo "  cat /tmp/moltbook_api_automation.json"
echo ""
echo "✅ 完成！"
