#!/bin/bash
# OpenClaw 博主监控脚本
# 运行频率: 每日 2 次 (12:00, 20:00)

REPORT_DIR="$HOME/.openclaw/workspace/reports/influencer-monitor"
DATE=$(date +%Y%m%d_%H%M)
REPORT_FILE="$REPORT_DIR/report_$DATE.md"

mkdir -p "$REPORT_DIR"

echo "# OpenClaw 博主监控报告 - $(date)" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# ===== 核心人物监控 =====
echo "## 🌟 核心人物动态" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Peter Steinberger (OpenClaw 创造者)
echo "### @steipete (Peter Steinberger)" >> "$REPORT_FILE"
echo "```" >> "$REPORT_FILE"
~/.agent-reach/venv/bin/xreach search "from:steipete" --json 2>/dev/null | head -50 >> "$REPORT_FILE" || echo "无法获取 X 内容" >> "$REPORT_FILE"
echo "```" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# ===== GitHub 热门项目更新 =====
echo "## 📊 GitHub 热门项目更新" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 获取最近更新的 OpenClaw 相关仓库
echo "### 最近更新的项目" >> "$REPORT_FILE"
echo "```" >> "$REPORT_FILE"
/usr/bin/gh search repos "OpenClaw" --sort updated --limit 10 2>/dev/null >> "$REPORT_FILE" || echo "GitHub API 限制" >> "$REPORT_FILE"
echo "```" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# ===== Exa 全网搜索 =====
echo "## 🔍 全网新内容" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 搜索最近24小时的 OpenClaw 相关内容
echo "### 最新文章/讨论" >> "$REPORT_FILE"
echo "```" >> "$REPORT_FILE"
mcporter call 'exa.web_search_exa({"query": "OpenClaw AI agent after:2026-03-04", "num_results": 5})' 2>/dev/null | head -100 >> "$REPORT_FILE" || echo "Exa 搜索暂不可用" >> "$REPORT_FILE"
echo "```" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# ===== 内容摘要 =====
echo "## 📝 内容摘要" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "- 监控时间: $(date)" >> "$REPORT_FILE"
echo "- 报告位置: $REPORT_FILE" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "监控完成: $REPORT_FILE"
