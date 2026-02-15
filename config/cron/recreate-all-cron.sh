#!/bin/bash
# 重建所有Cron任务
# 用法: ./recreate-all-cron.sh

echo "🔧 重建森森的所有Cron任务..."

# 注意: 这里使用openclaw命令重建任务
# 实际使用时可能需要根据openclaw的API调整

openclaw cron add --name="github-backup-sync" --schedule="*/30 * * * *" --command="github-backup"
openclaw cron add --name="evolution-light-2h" --schedule="0 */2 * * *" --command="evolution-light"
openclaw cron add --name="evolution-full-4h" --schedule="0 1,5,9,13,17,21 * * *" --command="evolution-full"
openclaw cron add --name="health-check-30min" --schedule="0 */2 * * *" --command="health-check"
openclaw cron add --name="deep-learning-loop" --schedule="0 2,14 * * *" --command="deep-learning"
openclaw cron add --name="moltbook-deep-scan" --schedule="0 */4 * * *" --command="moltbook-scan"
openclaw cron add --name="night-evolution-1" --schedule="0 23 * * *" --command="night-evolution-1"
openclaw cron add --name="night-evolution-2" --schedule="0 1 * * *" --command="night-evolution-2"
openclaw cron add --name="night-evolution-3" --schedule="0 3 * * *" --command="night-evolution-3"
openclaw cron add --name="full-backup-daily" --schedule="0 3 * * *" --command="full-backup"
openclaw cron add --name="daily-disk-cleanup" --schedule="0 3 * * *" --command="disk-cleanup"

echo "✅ Cron任务重建完成"
