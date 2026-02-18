#!/bin/bash
# 智能路由包装器 - 为Cron任务自动选择模型
# 用法: ./run-with-route.sh <task_type> <command>

set -e

WORKSPACE="/root/.openclaw/workspace"
ROUTE_PY="$WORKSPACE/scripts/route.py"

# 检查参数
if [ $# -lt 2 ]; then
    echo "用法: $0 <task_type> <command> [args...]"
    echo ""
    echo "示例:"
    echo "  $0 unified-monitor python3 scripts/unified-monitor.py --fix"
    echo "  $0 moltbook-scan python3 scripts/moltbook-unified-scan.py"
    echo "  $0 deep-learning python3 scripts/evolution-loop.py"
    echo ""
    echo "可用的task_type:"
    echo "  unified-monitor    / heartbeat   / monitor"
    echo "  maintenance"
    echo "  moltbook / scan / hn / github"
    echo "  deep / code / architecture"
    exit 1
fi

TASK_TYPE="$1"
shift
COMMAND="$@"

# 获取路由建议
ROUTE_OUTPUT=$(python3 "$ROUTE_PY" "$TASK_TYPE" 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ 路由失败，使用默认配置"
    MODEL="nvidia-build/stepfun-ai/step-3.5-flash"
    THINKING="off"
else
    # 提取模型和thinking（简化解析）
    MODEL=$(echo "$ROUTE_OUTPUT" | grep "完整路径:" | cut -d' ' -f3)
    THINKING=$(echo "$ROUTE_OUTPUT" | grep "Thinking:" | awk '{print $2}')
    REASON=$(echo "$ROUTE_OUTPUT" | grep "原因:" | cut -d' ' -f2-)
fi

echo "="
echo "🧠 智能路由: $TASK_TYPE"
echo "📌 模型: $MODEL"
echo "💭 Thinking: $THINKING"
if [ -n "$REASON" ]; then
    echo "📝 原因: $REASON"
fi
echo "="
echo "🚀 执行命令: $COMMAND"
echo "="

# 导出环境变量供子进程使用
export OPENCLAW_MODEL="$MODEL"
export OPENCLAW_THINKING="$THINKING"

# 执行命令
exec $COMMAND
