#!/bin/bash
# Moltbook 真社交自动化 - 定时任务脚本

export PATH="/root/.nvm/versions/node/v22.22.0/bin:$PATH"
cd /root/.openclaw/workspace

python3 scripts/moltbook_social_v41.py >> logs/moltbook_social.log 2>&1
