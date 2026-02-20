#!/bin/bash
# 清理并重新安装时段调度定时任务

# 获取 crontab 并移除重复项
current_cron=$(crontab -l 2>/dev/null | grep -v "^#" | sort -u)

# 移除所有 moltbook 相关任务
clean_cron=$(echo "$current_cron" | grep -v "moltbook")

# 添加新的时段调度任务
cat <<'CRON_NEW' >> /tmp/moltbook_final_cron.txt

# ============================================
# Moltbook 活跃时段 - 每30分钟高强度互动
# ============================================
0,30 9-11 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-active-hours.log 2>&1

0,30 14-16 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-active-hours.log 2>&1

0,30 20-22 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-active-hours.log 2>&1

# Moltbook 适中时段 - 每小时中等互动
0 8,12-13,17-19,23 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-moderate-hours.log 2>&1

# Moltbook 轻量时段 - 每小时轻量互动
0 0-7 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-scheduled-browse.py >> /root/.openclaw/workspace/data/moltbook/cron-light-hours.log 2>&1

# Moltbook 活动统计 - 每30分钟
*/30 * * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-activity-tracker.py >> /root/.openclaw/workspace/data/moltbook/cron-activity.log 2>&1

# Moltbook 深度学习 - 每天9点
0 9 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/moltbook-deep-learning.py >> /root/.openclaw/workspace/data/moltbook/cron-deep-learning.log 2>&1

CRON_NEW

# 合并：非moltbook任务 + moltbook任务
echo "$clean_cron" > /tmp/final_crontab
cat /tmp/moltbook_final_cron.txt >> /tmp/final_crontab

# 安装
crontab /tmp/final_crontab

# 清理
rm -f /tmp/final_crontab /tmp/moltbook_final_cron.txt

echo "✅ 时段调度已安装"
echo ""
echo "定时任务明细："
echo "  活跃时段: 9-11, 14-16, 20-22 (每30分钟)"
echo "  适中时段: 8, 12-13, 17-19, 23 (每小时)"
echo "  轻量时段: 0-7 (每小时)"
echo ""
