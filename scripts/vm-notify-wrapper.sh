#!/bin/bash
#
# VM状态监控通知器 - 双渠道版
# 包装脚本，同时发送飞书和Telegram通知
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$SCRIPT_DIR/.."

# 执行监控脚本并捕获输出
OUTPUT=$($SCRIPT_DIR/vm-status-monitor.sh 2>&1)
EXIT_CODE=$?

# 检查是否有通知内容（包含VM上线/离线信息）
if echo "$OUTPUT" | grep -q "VM已上线\|VM已离线"; then
    # 提取飞书消息（主要内容）
    FEISHU_MSG=$(echo "$OUTPUT" | sed -n '/^🌱\|^⚠️/,/^$/p' | head -20)
    
    # 提取Telegram消息
    TG_MSG=$(echo "$OUTPUT" | sed -n '/===TELEGRAM_NOTIFICATION===/,/===END_TELEGRAM===/p' | sed 's/===.*===//g')
    
    # 输出飞书消息（通过stdout，cron会发送到飞书）
    echo "$FEISHU_MSG"
    
    # 尝试通过message工具发送Telegram通知
    if command -v openclaw &> /dev/null && [ -n "$TG_MSG" ]; then
        # 使用非阻塞方式发送Telegram
        (openclaw message send --channel telegram --message "$TG_MSG" 2>/dev/null || true) &
    fi
fi

# 输出原始日志
echo "$OUTPUT"

exit $EXIT_CODE
