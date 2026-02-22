#!/bin/bash
# Moltbook 社交自动化 v6.0 - 安全执行脚本
# 
# 执行流程：
# 1. 扫描需要回复的评论
# 2. 使用 sessions_spawn 生成回复（每个回复独立调用）
# 3. 验证回复内容安全
# 4. 发送回复
# 5. 记录状态

cd /root/.openclaw/workspace

export PATH="/root/.nvm/versions/node/v22.22.0/bin:$PATH"

# 首先扫描待回复任务
python3 scripts/moltbook_scanner_v60.py

# 检查是否有待处理任务
if [ ! -f /tmp/moltbook_pending_replies.json ]; then
    echo "没有待处理任务"
    exit 0
fi

# 读取任务并逐个处理
python3 scripts/moltbook_sender_v60.py
