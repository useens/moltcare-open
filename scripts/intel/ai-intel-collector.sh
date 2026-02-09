#!/bin/bash
# AI情报收集器 - 每日7点执行
# 收集AI前沿信息、技术动态、最佳实践

set -e

WORKSPACE="/root/.openclaw/workspace"
INTEL_DIR="$WORKSPACE/memory/intel"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== AI情报收集开始 $DATE ==="

# 1. Hacker News 热门AI话题
echo "[1/5] 收集 Hacker News AI话题..."
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=AI+agent&tags=story&hitsPerPage=10" > "$INTEL_DIR/hn_ai_${DATE}.json" 2>/dev/null || echo "  - HN API 失败"

# 2. GitHub Trending (AI相关)
echo "[2/5] 收集 GitHub Trending..."
for topic in "ai-agent" "llm" "openclaw"; do
    curl -s "https://api.github.com/search/repositories?q=$topic+created:>$(date -d '7 days ago' +%Y-%m-%d)&sort=stars&order=desc&per_page=5" > "$INTEL_DIR/github_${topic}_${DATE}.json" 2>/dev/null || echo "  - GitHub $topic 失败"
done

# 3. arXiv 最新论文 (AI类别)
echo "[3/5] 收集 arXiv 论文..."
curl -s "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=5" > "$INTEL_DIR/arxiv_ai_${DATE}.xml" 2>/dev/null || echo "  - arXiv 失败"

# 4. 技术博客 RSS (简化版，实际可用rss2json等服务)
echo "[4/5] 技术博客检查..."
BLOGS=(
    "https://openai.com/blog/rss.xml"
    "https://www.anthropic.com/rss.xml"
    "https://blog.google/technology/ai/rss/"
)
for blog in "${BLOGS[@]}"; do
    curl -s "$blog" > "$INTEL_DIR/blog_$(echo $blog | md5sum | cut -c1-8)_${DATE}.xml" 2>/dev/null || echo "  - RSS 失败: $blog"
done

# 5. 生成情报摘要
echo "[5/5] 生成情报摘要..."
cat > "$INTEL_DIR/daily_digest_${DATE}.md" << EOF
# AI情报日报 - $DATE

## 收集时间
$(date '+%Y-%m-%d %H:%M:%S %Z')

## 数据来源
- [x] Hacker News AI话题
- [x] GitHub Trending (ai-agent, llm, openclaw)
- [x] arXiv cs.AI 最新论文
- [x] 技术博客 RSS

## 原始文件
$(ls -la $INTEL_DIR/*_${DATE}.* 2>/dev/null | wc -l) 个数据文件

## 待处理
等待agent分析提取关键信息：
1. 新技能发现
2. 安全威胁情报
3. 最佳实践更新
4. 技术趋势洞察

---
*自动收集，人工分析*
EOF

echo "=== 情报收集完成 ==="
echo "文件位置: $INTEL_DIR/"
ls -lh $INTEL_DIR/*_${DATE}.* 2>/dev/null || echo "警告: 无数据文件生成"
