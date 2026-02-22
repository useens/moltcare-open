#!/bin/bash
# Moltbook 社交自动化 v6.0 - 安全修复版 Cron 脚本
# 修复内容：
# - 使用安全的启发式回复（不使用CLI调用AI）
# - 严格内容验证
# - 移除所有模板风险

export PATH="/root/.nvm/versions/node/v22.22.0/bin:$PATH"
cd /root/.openclaw/workspace

# 每30分钟运行一次（安全频率）
python3 scripts/moltbook_social_v60.py >> logs/moltbook_social.log 2>&1
