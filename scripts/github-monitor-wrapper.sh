#!/bin/bash
# GitHub监控包装器 - 由NB02执行
NODE="NB02"
LOG_FILE="/root/.openclaw/workspace/nanobots/nb02/logs/github-monitor.log"
DATA_FILE="/root/.openclaw/workspace/nanobots/nb02/data/github-daily.json"

echo "[$NODE] $(date) 开始GitHub监控" >> "$LOG_FILE"

# 搜索OpenClaw相关repo
gh search repos "OpenClaw" --sort updated --limit 20 --json name,owner,updatedAt,url 2>/dev/null > "$DATA_FILE"

# 搜索AI Agent相关repo
gh search repos "AI Agent" "OpenClaw" --sort stars --limit 10 --json name,owner,stargazersCount,url 2>/dev/null >> "$DATA_FILE"

echo "[$NODE] $(date) GitHub监控完成，发现 $(jq length $DATA_FILE 2>/dev/null || echo 0) 个repo" >> "$LOG_FILE"
