#!/bin/bash
#
# 安装 Moltbook 自动化定时任务
#

echo "============================================================"
echo "🦞 Moltbook 自动化定时任务安装"
echo "============================================================"
echo ""

# 获取当前用户的crontab
echo "📋 读取当前crontab..."
current_cron=$(crontab -l 2>/dev/null || echo "")

# 检查是否已经安装
if echo "$current_cron" | grep -q "moltbook-daily-routine.py"; then
    echo "⚠️  检测到Moltbook定时任务已安装"
    echo ""
    read -p "是否要重新安装？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 安装已取消"
        exit 0
    fi

    # 移除旧的moltbook任务
    new_cron=$(echo "$current_cron" | grep -v "moltbook-")
else
    new_cron="$current_cron"
fi

# 添加新的定时任务
echo ""
echo "📝 添加定时任务..."

cat <<'CRON_TASKS' >> /tmp/cron_add.txt

# Moltbook Daily Routine (每小时)
0 * * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-daily-routine.py >> /root/.openclaw/workspace/data/moltbook/cron-daily-routine.log 2>&1

# Moltbook Activity Tracker (每30分钟)
*/30 * * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-activity-tracker.py >> /root/.openclaw/workspace/data/moltbook/cron-activity.log 2>&1

# Moltbook Deep Learning (每天早上9点)
0 9 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-deep-learning.py >> /root/.openclaw/workspace/data/moltbook/cron-deep-learning.log 2>&1

CRON_TASKS

# 合并新旧任务
echo "$new_cron" | cat - /tmp/cron_add.txt > /tmp/new_crontab

# 安装新的crontab
echo ""
echo "🔧 安装crontab..."
crontab /tmp/new_crontab

# 清理临时文件
rm -f /tmp/cron_add.txt /tmp/new_crontab

echo ""
echo "✅ 安装完成！"
echo ""
echo "已添加的定时任务:"
echo "  • 每小时: 浏览+点赞 (moltbook-daily-routine.py)"
echo "  • 每30分钟: 活动统计 (moltbook-activity-tracker.py)"
echo "  • 每天9点: 深度学习 (moltbook-deep-learning.py)"
echo ""
echo "查看当前crontab:"
echo "  $ crontab -l"
echo ""
echo "查看日志:"
echo "  $ ls -lh /root/.openclaw/workspace/data/moltbook/"
echo ""
echo "============================================================"
