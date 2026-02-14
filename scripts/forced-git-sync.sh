#!/bin/bash
# 强制Git同步脚本 - 云端节点
# 频率：每60秒执行一次

cd /root/.openclaw/workspace || exit 1

# 获取当前提交的hash（用于判断是否有更新）
BEFORE=$(git rev-parse HEAD)

# 强制同步（丢弃本地未提交更改，确保与GitHub完全一致）
git fetch origin main >/dev/null 2>&1
git reset --hard origin/main >/dev/null 2>&1

# 获取同步后的hash
AFTER=$(git rev-parse HEAD)

# 如果有更新，记录日志
if [ "$BEFORE" != "$AFTER" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 同步完成: $BEFORE -> $AFTER" >> memory/git-sync.log
    
    # 检查是否有来自备节点的新消息
    NEW_MESSAGES=$(find .messages/standby_to_primary/ -name "MSG-*.json" -newer .git/FETCH_HEAD 2>/dev/null | wc -l)
    
    if [ "$NEW_MESSAGES" -gt 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 发现 $NEW_MESSAGES 条新消息" >> memory/git-sync.log
        # 通知主session处理（通过文件标记）
        touch .messages/NEW_MESSAGES_PENDING
    fi
fi

# 保留最近1000行日志
tail -n 1000 memory/git-sync.log > memory/git-sync.log.tmp && mv memory/git-sync.log.tmp memory/git-sync.log