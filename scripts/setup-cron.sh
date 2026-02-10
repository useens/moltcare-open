#!/bin/bash
# 林林 v5.0 自我诊断系统 - Crontab配置脚本

set -e

WORKSPACE="/root/.openclaw/workspace"
SCRIPT_PATH="$WORKSPACE/scripts/health-monitor-v5.py"
LOG_PATH="$WORKSPACE/logs/cron-health.log"
CRON_JOB="*/10 * * * * /usr/bin/python3 $SCRIPT_PATH >> $LOG_PATH 2>&1"

echo "=============================================="
echo "林林 v5.0 自我诊断系统 - Crontab配置"
echo "=============================================="
echo ""

# 检查脚本是否存在
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "错误: 脚本不存在: $SCRIPT_PATH"
    exit 1
fi

# 检查是否已存在相同的cron任务
echo "[1/2] 检查现有cron任务..."
CURRENT_CRON=$(crontab -l 2>/dev/null || true)

if echo "$CURRENT_CRON" | grep -q "health-monitor-v5.py"; then
    echo "⚠️  已存在health-monitor-v5.py的cron任务"
    echo ""
    echo "现有任务:"
    echo "$CURRENT_CRON" | grep "health-monitor-v5.py"
    echo ""
    read -p "是否替换? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 删除旧任务
        NEW_CRON=$(echo "$CURRENT_CRON" | grep -v "health-monitor-v5.py")
        echo "$NEW_CRON" | crontab -
        echo "✓ 旧任务已删除"
    else
        echo "取消配置"
        exit 0
    fi
fi

# 添加新的cron任务
echo ""
echo "[2/2] 添加新的cron任务..."
echo ""
echo "将添加以下定时任务:"
echo "  频率: 每10分钟"
echo "  命令: $CRON_JOB"
echo ""

# 获取现有cron并添加新任务
if [ -z "$CURRENT_CRON" ]; then
    # 没有现有任务
    echo "$CRON_JOB" | crontab -
else
    # 追加到现有任务
    (echo "$CURRENT_CRON"; echo "$CRON_JOB") | crontab -
fi

echo "✓ Cron任务已添加"
echo ""

# 验证
echo "当前crontab内容:"
echo "----------------------------------------"
crontab -l | grep -E "(^#|health-monitor)" || echo "(无匹配内容)"
echo "----------------------------------------"
echo ""

# 测试运行
echo "是否立即测试运行一次? (y/n): "
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "运行测试..."
    /usr/bin/python3 "$SCRIPT_PATH"
    echo ""
    echo "✓ 测试完成"
fi

echo ""
echo "=============================================="
echo "配置完成！"
echo "=============================================="
echo ""
echo "监控将每10分钟自动运行一次"
echo ""
echo "查看日志:"
echo "  tail -f $LOG_PATH"
echo ""
echo "手动运行诊断:"
echo "  python3 $WORKSPACE/scripts/self-diagnosis.py"
echo ""
echo "手动运行修复:"
echo "  python3 $WORKSPACE/scripts/auto-heal.py"
echo ""
