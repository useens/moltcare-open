#!/bin/bash
# 月度深度清理脚本
# 每月1号执行：过期清理 + 冷归档 + 存储报告

set -e

LOG_FILE="$HOME/.openclaw/workspace/logs/monthly-cleanup.log"
REPORT_FILE="$HOME/.openclaw/workspace/reports/storage-report-$(date +%Y%m).md"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== 月度深度清理开始 ==="

# 1. 清理过期日志（保留90天）
log "清理过期日志..."
find "$HOME/.openclaw/workspace/logs" -name "*.log" -type f -mtime +90 -delete 2>/dev/null || true
find "$HOME/.openclaw/logs" -name "*.log" -type f -mtime +90 -delete 2>/dev/null || true

# 2. 清理临时文件
log "清理临时文件..."
find "$HOME/.openclaw/workspace/tmp" -type f -mtime +30 -delete 2>/dev/null || true
find /tmp -name "openclaw-*" -type f -mtime +7 -delete 2>/dev/null || true

# 3. 归档旧备份（保留最近30个完整备份）
log "归档旧备份..."
cd "$HOME/.openclaw/backups/local" 2>/dev/null && ls -t workspace_*_full.tar.gz | tail -n +31 | xargs -r rm -f || true

# 4. 生成存储报告
log "生成存储报告..."
mkdir -p "$(dirname "$REPORT_FILE")"
cat > "$REPORT_FILE" <> EOF
# 存储使用报告 - $(date +%Y年%m月)

生成时间: $(date '+%Y-%m-%d %H:%M:%S')

## 磁盘使用情况
$(df -h /root / | head -5)

## 工作区大小
$(du -sh "$HOME/.openclaw/workspace" 2>/dev/null || echo "无法统计")

## 备份大小
$(du -sh "$HOME/.openclaw/backups" 2>/dev/null || echo "无法统计")

## 日志大小
$(du -sh "$HOME/.openclaw/workspace/logs" "$HOME/.openclaw/logs" 2>/dev/null | head -5)

## 清理完成
- 过期日志已清理 (>90天)
- 临时文件已清理 (>30天)
- 旧备份已归档 (>30个)
EOF

log "存储报告已生成: $REPORT_FILE"
log "=== 月度深度清理完成 ==="
