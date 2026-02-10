#!/bin/bash
# 夜间情报收集 - 浏览器提取版

echo "🌙 夜间情报收集（浏览器提取）"
DATE=$(date +%Y%m%d_%H%M%S)
OUTDIR="/root/.openclaw/workspace/memory/intel"
mkdir -p "$OUTDIR"

# 1. Moltbook 热门
echo "📡 提取 Moltbook..."
python3 /root/.openclaw/workspace/scripts/moltbook-super-extractor.py hot > "$OUTDIR/moltbook_${DATE}.json" 2>/dev/null || echo "⚠️ Moltbook 提取失败"

# 2. GitHub Trending
echo "📡 提取 GitHub Trending..."
python3 /root/.openclaw/workspace/scripts/web-extractor/github_trending.py > "$OUTDIR/github_${DATE}.json" 2>/dev/null || echo "⚠️ GitHub 提取失败"

# 3. HackerNews (原有 API 方式)
echo "📡 提取 HackerNews..."
curl -s "https://hacker-news.firebaseio.com/v0/topstories.json" | \
    jq -r '.[0:10][]' | \
    xargs -I {} curl -s "https://hacker-news.firebaseio.com/v0/item/{}.json" > "$OUTDIR/hn_${DATE}.jsonl"

echo "✅ 收集完成: $OUTDIR"
