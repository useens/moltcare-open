#!/bin/bash
# Moltbook 社交自动化 - 快速启动脚本

echo "🚀 启动 Moltbook 社交自动化"
echo "================================"
echo ""

# 检查凭证
if [ ! -f /root/.config/moltbook/credentials.json ]; then
    echo "❌ 错误: 凭证文件不存在"
    exit 1
fi

# 运行社交自动化
echo "🤖 运行社交自动化脚本..."
python3 /root/.openclaw/workspace/scripts/moltbook-social-automation.py

echo ""
echo "📝 查看回复草稿:"
echo "  cat /root/.openclaw/workspace/moltbook-replies-draft.md"
echo ""
echo "📊 查看活动日志:"
echo "  tail -20 /root/.openclaw/workspace/data/moltbook/activity-log.jsonl"
echo ""
echo "✅ 完成！"
