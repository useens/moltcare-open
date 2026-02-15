#!/bin/bash
# Token使用监控脚本 - 生成每日Token消耗报告
# 运行时间: 每天23:55

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE/logs/token-usage-daily.log"
REPORT_FILE="$WORKSPACE/reports/token-usage-daily.md"
DATE=$(date '+%Y-%m-%d')

# 计算今日会话数
SESSION_COUNT=$(ls -la $WORKSPACE/memory/heartbeat-state.json 2>/dev/null | wc -l)

# 计算日志增长
LOG_SIZE=$(du -sb $WORKSPACE/logs 2>/dev/null | cut -f1)
REPORT_SIZE=$(du -sb $WORKSPACE/reports 2>/dev/null | cut -f1)
MEMORY_SIZE=$(du -sb $WORKSPACE/memory 2>/dev/null | cut -f1)

# 计算Cron任务数
CRON_COUNT=$(crontab -l 2>/dev/null | grep -v '^#' | grep -v '^$' | wc -l)

# 计算Python进程数
PYTHON_PROCS=$(ps aux | grep python | grep -v grep | wc -l)

# 生成报告
cat > $REPORT_FILE << EOF
# Token使用日报 - $DATE

## 📊 系统资源占用

| 指标 | 数值 |
|------|------|
| 日志目录大小 | $(du -sh $WORKSPACE/logs 2>/dev/null | cut -f1) |
| 报告目录大小 | $(du -sh $WORKSPACE/reports 2>/dev/null | cut -f1) |
| 记忆目录大小 | $(du -sh $WORKSPACE/memory 2>/dev/null | cut -f1) |
| Cron任务数 | $CRON_COUNT |
| Python进程数 | $PYTHON_PROCS |

## 🔔 预警阈值

- 日志目录 > 5MB: 需要清理
- 报告目录 > 50MB: 需要归档
- Python进程 > 30: 需要检查

## 📝 记录时间

$DATE 23:55
EOF

echo "[$DATE] Token日报已生成: $REPORT_FILE" >> $LOG_FILE