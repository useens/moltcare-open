#!/bin/bash
#
# 快速检查真诚回复系统状态
#

echo "============================================================"
echo "🔍 真诚回复系统状态检查"
echo "============================================================"
echo ""
echo "时间: $(date '+%Y-%m-%d %H:%M:%S') UTC+8"
echo ""

# 检查监听器进程
echo "📊 进程状态:"
if pgrep -f "moltbook-reply-monitor.py" > /dev/null; then
    echo "  ✅ 回复监听器: 运行中"
    PID=$(pgrep -f "moltbook-reply-monitor.py")
    echo "     PID: $PID"
else
    echo "  ❌ 回复监听器: 未运行"
fi
echo ""

# 检查我的评论
echo "📝 我的评论:"
if [ -f "/root/.openclaw/workspace/data/moltbook/activity-log.jsonl" ]; then
    comment_count=$(grep -c '"type": "comment"' /root/.openclaw/workspace/data/moltbook/activity-log.jsonl 2>/dev/null || echo "0")
    echo "  已发布评论: $comment_count 条"
else
    echo "  暂无评论记录"
fi
echo ""

# 检查回复历史
echo "💬 回复历史:"
if [ -f "/root/.openclaw/workspace/data/moltbook/replied-log.jsonl" ]; then
    reply_count=$(wc -l < /root/.openclaw/workspace/data/moltbook/replied-log.jsonl)
    echo "  已真诚回复: $reply_count 条"
    if [ "$reply_count" -gt 0 ]; then
        echo ""
        echo "  最近的 3 条回复:"
        tail -3 /root/.openclaw/workspace/data/moltbook/replied-log.jsonl | head -3
    fi
else
    echo "  暂无回复记录"
fi
echo ""

# 显示日志文件的最后几行
echo "📋 监听器日志 (最近 5 行):"
if [ -f "/root/.openclaw/workspace/data/moltbook/reply-monitor.log" ]; then
    tail -5 /root/.openclaw/workspace/data/moltbook/reply-monitor.log
else
    echo "  日志文件尚不存在"
fi
echo ""

echo "============================================================"
echo "💡 快速命令:"
echo "============================================================"
echo "  # 查看完整日志"
echo "  tail -f data/moltbook/reply-monitor.log"
echo ""
echo "  # 手动检查新回复"
echo "  python3 scripts/moltbook-reply-monitor.py --once"
echo ""
echo "  # 启动/重启监听器"
echo "  nohup python3 scripts/moltbook-reply-monitor.py >> data/moltbook/reply-monitor.log 2>&1 &"
echo "  # 或"
echo "  bash scripts/start-reply-monitor.sh"
echo ""
echo "============================================================"
echo "✅ 文档位置:"
echo "============================================================"
echo "  📖 真诚回复指南: docs/moltbook-sincere-reply-guide.md"
echo "  📊 执行报告: data/moltbook/SINCERE_REPLY_REPORT.md"
echo ""
echo "============================================================"
