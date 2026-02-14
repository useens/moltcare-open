#!/bin/bash
# =============================================================================
# 系统自动化任务调度 - System Automation Cron Setup
# 安装自动化任务的脚本
# =============================================================================

WORKSPACE="/root/.openclaw/workspace"
LOGS_DIR="$WORKSPACE/logs"

echo "=========================================="
echo "🤖 系统自动化任务调度设置"
echo "=========================================="
echo ""

# 创建日志目录
mkdir -p "$LOGS_DIR/automation"

# 生成crontab内容
cat > /tmp/automation-cron.txt << 'EOF'
# ============================================
# 森森系统自动化任务 - 自动生成
# 配置时间: $(date)
# ============================================

# ----------------- 日志自动化管理 -----------------
# 每天凌晨2:00执行日志清理和归档
0 2 * * * cd /root/.openclaw/workspace && /usr/bin/python3 scripts/auto-log-manager.py >> /root/.openclaw/workspace/logs/automation/log-manager.log 2>&1

# ----------------- 备份检查与修复 -----------------
# 每6小时检查备份完整性
0 */6 * * * cd /root/.openclaw/workspace && /usr/bin/python3 scripts/auto-backup-check.py >> /root/.openclaw/workspace/logs/automation/backup-check.log 2>&1

# ----------------- 健康检查自动化 -----------------
# 每10分钟执行健康检查
*/10 * * * * cd /root/.openclaw/workspace && /usr/bin/python3 scripts/auto-health-check.py >> /root/.openclaw/workspace/logs/automation/health-check.log 2>&1

# ----------------- 情报收集调度 -----------------
# 根据当前模式自动调整频率
# 正常模式: 每6小时
# 超进化模式: 每小时
0 */6 * * * cd /root/.openclaw/workspace && /usr/bin/python3 scripts/auto-intel-scheduler.py >> /root/.openclaw/workspace/logs/automation/intel-scheduler.log 2>&1

# ----------------- 监控仪表板生成 -----------------
# 每小时生成一次仪表板报告
0 * * * * cd /root/.openclaw/workspace && /usr/bin/python3 scripts/monitoring-dashboard.py --format json >> /root/.openclaw/workspace/logs/automation/dashboard.log 2>&1

# ----------------- 超进化模式支持 -----------------
# 在超进化模式下，每30分钟执行一次情报收集
*/30 * * * * cd /root/.openclaw/workspace && [ -f memory/hyper-evolution-state.json ] && grep -q '"active": true' memory/hyper-evolution-state.json && /usr/bin/python3 scripts/auto-intel-scheduler.py >> /root/.openclaw/workspace/logs/automation/intel-hyper.log 2>&1 || true

EOF

echo "✓ 自动化任务配置已生成"
echo ""
echo "配置文件位置: /tmp/automation-cron.txt"
echo ""
echo "要安装这些自动化任务，请执行:"
echo "  crontab /tmp/automation-cron.txt"
echo ""
echo "或者追加到现有crontab:"
echo "  crontab -l > /tmp/current-cron.txt"
echo "  cat /tmp/automation-cron.txt >> /tmp/current-cron.txt"
echo "  crontab /tmp/current-cron.txt"
echo ""
echo "=========================================="
