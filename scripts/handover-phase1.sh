#!/bin/bash
# 任务移交实施脚本 - Phase 1
# 将监控、收集、清理任务移交给10个小弟

WORKSPACE="/root/.openclaw/workspace"
SCRIPTS="$WORKSPACE/scripts"

echo "======================================================================"
echo "🤖 任务移交实施 - Phase 1"
echo "======================================================================"
echo ""

# 1. 配置Polymarket监控 -> NB04
echo "1️⃣  移交Polymarket监控给NB04..."
cat > "$SCRIPTS/polymarket-wrapper.sh" << 'EOF'
#!/bin/bash
# Polymarket监控包装器 - 由NB04执行
NODE="NB04"
LOG_FILE="/root/.openclaw/workspace/nanobots/nb04/logs/polymarket.log"

echo "[$NODE] $(date) 开始Polymarket监控" >> "$LOG_FILE"
cd /root/.openclaw/workspace
python3 scripts/polymarket_monitor.py >> "$LOG_FILE" 2>&1

# 检查异常，如果有则通知指挥中心
if grep -q "error\|exception\|timeout" "$LOG_FILE" | tail -5; then
    echo "[$NODE] $(date) 发现异常，通知指挥中心" >> "$LOG_FILE"
    python3 scripts/feishu-sync.py high "polymarket.monitor" "NB04检测到Polymarket异常" 2>/dev/null
fi
EOF
chmod +x "$SCRIPTS/polymarket-wrapper.sh"

# 添加到NB04的cron
echo "添加Polymarket监控到NB04..."
(crontab -l 2>/dev/null | grep -v "polymarket-wrapper"; echo "*/30 * * * * $SCRIPTS/polymarket-wrapper.sh") | crontab -
echo "   ✅ Polymarket监控已配置给NB04"
echo ""

# 2. 配置日志清理 -> NB05
echo "2️⃣  移交日志清理给NB05..."
cat > "$SCRIPTS/log-cleanup-wrapper.sh" << 'EOF'
#!/bin/bash
# 日志清理包装器 - 由NB05执行
NODE="NB05"
LOG_FILE="/root/.openclaw/workspace/nanobots/nb05/logs/cleanup.log"

echo "[$NODE] $(date) 开始日志清理" >> "$LOG_FILE"

# 清理旧日志
find /root/.openclaw/workspace/logs -name "*.log" -mtime +7 -delete 2>/dev/null
find /root/.openclaw/workspace/nanobots/*/logs -name "*.log" -mtime +3 -delete 2>/dev/null

# 清理旧快照
find /root/.openclaw/workspace/.snapshots -name "snapshot_*.tar.gz" -mtime +7 -delete 2>/dev/null

echo "[$NODE] $(date) 日志清理完成" >> "$LOG_FILE"
EOF
chmod +x "$SCRIPTS/log-cleanup-wrapper.sh"

# 添加到NB05的cron
echo "添加日志清理到NB05..."
(crontab -l 2>/dev/null | grep -v "log-cleanup-wrapper"; echo "0 4 * * * $SCRIPTS/log-cleanup-wrapper.sh") | crontab -
echo "   ✅ 日志清理已配置给NB05"
echo ""

# 3. 配置GitHub监控 -> NB02
echo "3️⃣  移交GitHub监控给NB02..."
cat > "$SCRIPTS/github-monitor-wrapper.sh" << 'EOF'
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
EOF
chmod +x "$SCRIPTS/github-monitor-wrapper.sh"

# 添加到NB02的cron
echo "添加GitHub监控到NB02..."
(crontab -l 2>/dev/null | grep -v "github-monitor-wrapper"; echo "0 8 * * * $SCRIPTS/github-monitor-wrapper.sh") | crontab -
echo "   ✅ GitHub监控已配置给NB02"
echo ""

# 4. 创建小弟自主健康检查
echo "4️⃣  配置小弟自主健康检查..."
cat > "$SCRIPTS/health-check-nanobot.py" << 'EOF'
#!/usr/bin/env python3
"""Nanobot健康检查 - 由NB05执行"""
import requests
import json
from datetime import datetime

NODES = [
    ("NB01", 18801), ("NB02", 18802), ("NB03", 18803),
    ("NB04", 18804), ("NB05", 18805), ("NB06", 18806),
    ("NB07", 18807), ("NB08", 18808), ("NB09", 18809), ("NB10", 18810)
]

def check_node(node_id, port):
    try:
        resp = requests.get(f"http://127.0.0.1:{port}/status", timeout=5)
        return resp.status_code == 200
    except:
        return False

results = {}
for node_id, port in NODES:
    results[node_id] = check_node(node_id, port)

# 记录结果
log_file = "/root/.openclaw/workspace/nanobots/nb05/logs/health-check.log"
with open(log_file, "a") as f:
    f.write(f"[{datetime.now().isoformat()}] Health check: {json.dumps(results)}\n")

# 如果有离线节点，通知指挥中心
offline = [n for n, status in results.items() if not status]
if offline:
    import subprocess
    subprocess.run([
        "python3", "/root/.openclaw/workspace/scripts/feishu-sync.py",
        "high", "health.monitor",
        f"节点离线: {', '.join(offline)}"
    ])
    print(f"⚠️  发现离线节点: {offline}")
else:
    print("✅ 所有节点在线")
EOF
chmod +x "$SCRIPTS/health-check-nanobot.py"

# 添加到NB05的cron
echo "添加健康检查到NB05..."
(crontab -l 2>/dev/null | grep -v "health-check-nanobot"; echo "*/5 * * * * /usr/bin/python3 $SCRIPTS/health-check-nanobot.py") | crontab -
echo "   ✅ 健康检查已配置给NB05"
echo ""

# 5. 清理旧的重复cron
echo "5️⃣  清理我原来的重复任务..."
# 删除已移交给小弟的任务
crontab -l 2>/dev/null | \
    grep -v "polymarket_monitor.py" | \
    grep -v "github-monitor" | \
    grep -v "find.*logs.*delete" | \
    crontab -
echo "   ✅ 已清理移交给小弟的cron任务"
echo ""

echo "======================================================================"
echo "✅ Phase 1 移交完成！"
echo "======================================================================"
echo ""
echo "移交总结:"
echo "  ✅ Polymarket监控 → NB04 (每30分钟)"
echo "  ✅ 日志清理 → NB05 (每天4点)"
echo "  ✅ GitHub监控 → NB02 (每天8点)"
echo "  ✅ 健康检查 → NB05 (每5分钟)"
echo ""
echo "我的新职责:"
echo "  🎯 只负责: 决策、分析、路由、指挥"
echo "  ❌ 不再执行: 监控、收集、清理等重复任务"
echo ""
echo "查看小弟状态: ./scripts/cc-node list"
echo "======================================================================"
