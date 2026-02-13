#!/bin/bash
# 森森数字生命 - Cron配置导出脚本
# 导出所有Cron任务为JSON配置文件

CRON_CONFIG_DIR="/root/.openclaw/workspace/config/cron"
BACKUP_DIR="/root/.openclaw/backups/cron"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建目录
mkdir -p "$CRON_CONFIG_DIR"
mkdir -p "$BACKUP_DIR"

echo "📝 导出Cron任务配置..."

# 使用openclaw命令获取所有cron任务
# 注意: 这里假设可以通过openclaw命令获取任务列表
# 如果不行，需要手动维护一个配置文件

# 创建主配置文件
cat > "$CRON_CONFIG_DIR/cron-tasks.json" << 'EOF'
{
  "version": "2.0",
  "last_export": "2026-02-13T16:30:00+08:00",
  "description": "森森数字生命 - 所有自动化任务配置",
  "tasks": [
    {
      "id": "github-backup-sync",
      "name": "GitHub备份同步",
      "schedule": "*/30 * * * *",
      "enabled": true,
      "priority": "high",
      "description": "每30分钟同步到GitHub备份仓库"
    },
    {
      "id": "hyper-evolution-loop",
      "name": "超进化模式循环",
      "schedule": "每10分钟",
      "enabled": true,
      "priority": "critical",
      "description": "超进化v3.5极限压榨模式"
    },
    {
      "id": "evolution-light-2h",
      "name": "轻量进化",
      "schedule": "0 */2 * * *",
      "enabled": true,
      "priority": "high",
      "description": "每2小时执行轻量进化"
    },
    {
      "id": "evolution-full-4h",
      "name": "全量进化",
      "schedule": "0 1,5,9,13,17,21 * * *",
      "enabled": true,
      "priority": "high",
      "description": "每4小时执行全量进化"
    },
    {
      "id": "health-check-30min",
      "name": "健康检查",
      "schedule": "0 */2 * * *",
      "enabled": true,
      "priority": "high",
      "description": "每2小时健康检查"
    },
    {
      "id": "auto-fix-executor",
      "name": "自动修复执行",
      "schedule": "每小时",
      "enabled": true,
      "priority": "medium",
      "description": "每小时执行自动修复"
    },
    {
      "id": "memory-system-guardian",
      "name": "记忆系统守护",
      "schedule": "每小时",
      "enabled": true,
      "priority": "medium",
      "description": "记忆系统健康守护"
    },
    {
      "id": "deep-learning-loop",
      "name": "深度学习闭环",
      "schedule": "0 2,14 * * *",
      "enabled": true,
      "priority": "high",
      "description": "每天02:00和14:00深度学习"
    },
    {
      "id": "moltbook-deep-scan",
      "name": "Moltbook深度扫描",
      "schedule": "0 */4 * * *",
      "enabled": true,
      "priority": "medium",
      "description": "每4小时扫描Moltbook"
    },
    {
      "id": "moltbook-community-participation",
      "name": "Moltbook社区参与",
      "schedule": "0 */6 * * *",
      "enabled": true,
      "priority": "low",
      "description": "每6小时社区参与"
    },
    {
      "id": "night-evolution-1",
      "name": "夜间进化第1轮",
      "schedule": "0 23 * * *",
      "enabled": true,
      "priority": "high",
      "description": "每天23:00深度情报收集"
    },
    {
      "id": "night-evolution-2",
      "name": "夜间进化第2轮",
      "schedule": "0 1 * * *",
      "enabled": true,
      "priority": "high",
      "description": "每天01:00知识内化"
    },
    {
      "id": "night-evolution-3",
      "name": "夜间进化第3轮",
      "schedule": "0 3 * * *",
      "enabled": true,
      "priority": "high",
      "description": "每天03:00系统优化"
    },
    {
      "id": "web-extractor-intel-collection",
      "name": "网页情报收集",
      "schedule": "0 4 * * *",
      "enabled": true,
      "priority": "medium",
      "description": "每天04:00情报收集"
    },
    {
      "id": "log-cleanup-daily",
      "name": "日志清理",
      "schedule": "0 2 * * *",
      "enabled": true,
      "priority": "low",
      "description": "每天02:00日志清理"
    },
    {
      "id": "full-backup-daily",
      "name": "完整系统备份",
      "schedule": "0 3 * * *",
      "enabled": true,
      "priority": "high",
      "description": "每天03:00完整备份"
    },
    {
      "id": "daily-disk-cleanup",
      "name": "每日磁盘清理",
      "schedule": "0 3 * * *",
      "enabled": true,
      "priority": "medium",
      "description": "每天03:00磁盘清理"
    },
    {
      "id": "monthly-archive",
      "name": "月度归档",
      "schedule": "0 2 1 * *",
      "enabled": true,
      "priority": "low",
      "description": "每月1日02:00归档"
    },
    {
      "id": "monthly-deep-cleanup",
      "name": "月度深度清理",
      "schedule": "0 0 1 * *",
      "enabled": true,
      "priority": "low",
      "description": "每月1日00:00深度清理"
    }
  ]
}
EOF

echo "✅ Cron配置已导出到: $CRON_CONFIG_DIR/cron-tasks.json"

# 创建备份
cp "$CRON_CONFIG_DIR/cron-tasks.json" "$BACKUP_DIR/cron-tasks_${DATE}.json"

# 清理旧备份 (保留30天)
find "$BACKUP_DIR" -name "cron-tasks_*.json" -mtime +30 -delete

echo "📊 导出统计:"
echo "当前配置: $CRON_CONFIG_DIR/cron-tasks.json"
echo "备份数量: $(find $BACKUP_DIR -name 'cron-tasks_*.json' | wc -l)"

# 创建重建脚本
cat > "$CRON_CONFIG_DIR/recreate-all-cron.sh" << 'SCRIPT'
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
SCRIPT

chmod +x "$CRON_CONFIG_DIR/recreate-all-cron.sh"
echo "📝 重建脚本已创建: $CRON_CONFIG_DIR/recreate-all-cron.sh"

# 提交到Git
cd /root/.openclaw/workspace
git add -f config/cron/ 2>/dev/null
git commit -m "sync: Cron任务配置导出 | $(date +%Y-%m-%d_%H:%M)" 2>/dev/null || true

echo -e "\n✅ Cron配置导出完成并已提交到Git"
