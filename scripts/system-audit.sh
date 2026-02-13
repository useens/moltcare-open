#!/bin/bash
# 系统审计工具
# 全面检查系统状态

echo "======================================================================"
echo "🔍 系统审计报告"
echo "======================================================================"
echo "审计时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

echo "【系统资源】"
echo "- CPU负载: $(uptime | awk -F'load average:' '{print $2}')"
echo "- 内存使用:"
free -h | grep "Mem:"
echo "- 磁盘使用:"
df -h / | tail -1
echo ""

echo "【关键进程】"
echo "- OpenClaw Gateway:"
pgrep -a openclaw | head -1 || echo "  未运行"
echo "- 超进化引擎:"
systemctl is-active hyper-evolution 2>/dev/null || echo "  状态未知"
echo ""

echo "【文件系统】"
echo "- 工作区文件数: $(find /root/.openclaw/workspace -type f 2>/dev/null | wc -l)"
echo "- 脚本数量: $(ls /root/.openclaw/workspace/scripts/*.py 2>/dev/null | wc -l)"
echo "- 报告数量: $(ls /root/.openclaw/workspace/reports/*.md 2>/dev/null | wc -l)"
echo ""

echo "【Git状态】"
cd /root/.openclaw/workspace
echo "- 分支: $(git branch --show-current 2>/dev/null || echo 'N/A')"
echo "- 最新提交: $(git log -1 --oneline 2>/dev/null || echo 'N/A')"
echo ""

echo "======================================================================"
echo "✅ 系统审计完成"
echo "======================================================================"
