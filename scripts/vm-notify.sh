#!/bin/bash
# VM状态变化通知脚本

STATE="$1"
TIME=$(date '+%Y-%m-%d %H:%M:%S')

if [ "$STATE" = "online" ]; then
    MESSAGE="🌱 VM已上线\n\n时间: $TIME\n状态: 双节点正常"
else
    MESSAGE="🚨 VM已离线\n\n时间: $TIME\n状态: 单节点运行"
fi

# Telegram
python3 -c "
import sys
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
# 这里调用Telegram通知API
print('Telegram通知: $STATE')
" 2>/dev/null || true

echo "$MESSAGE"
