#!/bin/bash
#
# 安装基于时段的 Moltbook 浏览定时任务
#

echo "============================================================"
echo "🦞 Moltbook 时段调度定时任务安装"
echo "============================================================"
echo ""

# 获取当前用户 crontab
current_cron=$(crontab -l 2>/dev/null || echo "")

# 移除旧的每小时互动任务
new_cron=$(echo "$current_cron" | grep -v "moltbook-hourly-interactive.py")
new_cron=$(echo "$new_cron" | grep -v "moltbook-daily-routine.py")

# 添加新的时段调度任务
cat <<'CRON_CONFIG' >> /tmp/moltbook_schedule_cron.txt

# ============================================
# Moltbook 活跃时段 - 每30分钟高强度互动
# 时段: 9-11, 14-16, 20-22 (每天)
# ============================================
0,30 9-11 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-active-hours.log 2>&1

0,30 14-16 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-active-hours.log 2>&1

0,30 20-22 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-active-hours.log 2>&1

# ============================================
# Moltbook 适中时段 - 每小时中等互动
# 时段: 8, 12-13, 17-19, 23 (每天)
# ============================================
0 8 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-moderate-hours.log 2>&1

0 12-13 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-moderate-hours.log 2>&1

0 17-19 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-moderate-hours.log 2>&1

0 23 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-moderate-hours.log 2>&1

# ============================================
# Moltbook 轻量时段 - 每小时轻量互动
# 时段: 0-7 (深夜到清晨)
# ============================================
0 0-7 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-light-hours.log 2>&1

# ============================================
# 保持其他 Moltbook 任务
# ============================================
# 每30分钟活动统计
*/30 * * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-activity-tracker.py >> /root/.openclaw/workspace/data/moltbook/cron-activity.log 2>&1

# 每天深度学习
0 9 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-deep-learning.py >> /root/.openclaw/workspace/data/moltbook/cron-deep-learning.log 2>&1

CRON_CONFIG

# 合并
echo "$new_cron" | cat - /tmp/moltbook_schedule_cron.txt > /tmp/new_crontab

# 安装
echo ""
echo "🔧 安装新的 crontab..."
crontab /tmp/new_crontab

# 清理
rm -f /tmp/moltbook_schedule_cron.txt /tmp/new_crontab

echo ""
echo "✅ 安装完成！"
echo ""
echo "📅 时段调度配置:"
echo "  🟢 活跃时段 (每30分钟): 09:00-11:00, 14:00-16:00, 20:00-22:00"
echo "  🟡 适中时段 (每小時):   08:00, 12:00-13:00, 17:00-19:00, 23:00"
echo "  🔵 轻量时段 (每小時):   00:00-07:00"
echo ""
echo "🔋 预计每天运行: 23 次"
echo ""
echo "查看定时任务:"
echo "  $ crontab -l"
echo ""
echo "查看时段日志:"
echo "  $ tail -20 data/moltbook/cron-active-hours.log"
echo "  $ tail -20 data/moltbook/cron-moderate-hours.log"
echo "  $ tail -20 data/moltbook/cron-light-hours.log"
echo ""
echo "============================================================"
