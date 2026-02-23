#!/bin/bash
# Moltbook 自然社交 Cron 脚本
# 每30分钟执行一次

export PATH="/root/.nvm/versions/node/v22.22.0/bin:$PATH"
cd /root/.openclaw/workspace

# 执行自然社交自动脚本
python3 scripts/moltbook-natural-social-auto.py >> /root/.openclaw/workspace/data/moltbook/natural-social-cron.log 2>&1
