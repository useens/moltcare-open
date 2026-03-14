#!/bin/bash
# MoltCare Daily Analysis - 每天分析并决定应用

YESTERDAY=$(date -d "yesterday" +%Y%m%d)
DATE=$(date +%Y%m%d)

WORK_DIR="$HOME/.openclaw/workspace/moltcare-open/research/daily/$YESTERDAY"
REPORT_FILE="$HOME/.openclaw/workspace/moltcare-open/research/analysis_${YESTERDAY}.md"

echo "🦞 Daily Analysis Report"
echo "========================"
echo "分析日期: $YESTERDAY"
echo "生成时间: $(date)"
echo ""

# 检查是否有昨天的数据
if [ ! -d "$WORK_DIR/raw" ]; then
    echo "⚠️  昨天没有搜索数据"
    exit 0
fi

# 汇总所有搜索结果
echo "📊 24小时搜索汇总"
echo "-------------------"
TOTAL_HIGH=0
cat "$WORK_DIR/raw"/github_*.json 2>/dev/null | python3 -c "
import sys, json, glob, os

all_items = []
for line in sys.stdin:
    try:
        data = json.loads(line)
        items = data.get('items', [])
        all_items.extend(items)
    except:
        pass

# 去重并按 stars 排序
seen = set()
unique_items = []
for item in all_items:
    name = item.get('full_name', '')
    if name and name not in seen:
        seen.add(name)
        unique_items.append(item)

unique_items.sort(key=lambda x: x['stargazers_count'], reverse=True)

# 输出统计
high_value = [i for i in unique_items if i['stargazers_count'] > 1000]
med_value = [i for i in unique_items if 100 <= i['stargazers_count'] <= 1000]

print(f'总发现仓库: {len(unique_items)}')
print(f'🔥 高价值(>1k⭐): {len(high_value)}')
print(f'⭐ 中价值(100-1k⭐): {len(med_value)}')
print()

# 输出高价值列表
if high_value:
    print('### 高价值发现 (需要分析)')
    print()
    for i, item in enumerate(high_value[:10], 1):
        print(f\"{i}. **{item['full_name']}** ({item['stargazers_count']}⭐)\")
        print(f\"   {item.get('description', 'No description')[:80]}\")
        print(f\"   🔗 {item['html_url']}\")
        print()

print(f'__HIGH_COUNT__:{len(high_value)}')
" > /tmp/daily_summary.txt

cat /tmp/daily_summary.txt | grep -v "__HIGH_COUNT__"
TOTAL_HIGH=$(cat /tmp/daily_summary.txt | grep "__HIGH_COUNT__" | cut -d: -f2)

# 生成分析报告
cat > "$REPORT_FILE" << EOF
# Daily Analysis Report - $YESTERDAY

**分析时间**: $(date)
**数据来源**: 24小时 GitHub 搜索汇总

---

## 搜索统计

$(cat /tmp/daily_summary.txt | grep -v "__HIGH_COUNT__")

---

## 分析结论

### 需要深度分析的高价值仓库: $TOTAL_HIGH

EOF

# 为每个高价值仓库创建分析任务
if [ "$TOTAL_HIGH" -gt 0 ]; then
    echo "### 待分析列表" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    cat /tmp/daily_summary.txt | grep "^\d\." | head -10 | while read -r line; do
        repo=$(echo "$line" | grep -oP '(?<=\*\*)[^*]+(?=\*\*)')
        echo "- [ ] 分析 $repo" >> "$REPORT_FILE"
    done
    
    echo "" >> "$REPORT_FILE"
    echo "### 分析标准" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "对每个高价值仓库:" >> "$REPORT_FILE"
    echo "1. 读取 README 和核心文件" >> "$REPORT_FILE"
    echo "2. 提取可复用的设计模式" >> "$REPORT_FILE"
    echo "3. 判断是否适合应用到 moltcare-open" >> "$REPORT_FILE"
    echo "4. 如适合，创建应用计划" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" <> 'EOF'

## 下一步

- [ ] 手动审查高价值仓库
- [ ] 提取精华元素
- [ ] 应用到 moltcare-open GitHub 仓库
- [ ] 提交 PR 或更新

---

*自动生成于 $(date)*
EOF

echo ""
echo "📄 分析报告已生成: $REPORT_FILE"
echo ""

if [ "$TOTAL_HIGH" -gt 0 ]; then
    echo "🔥 发现 $TOTAL_HIGH 个高价值仓库需要分析"
    echo "   请查看报告并开始深度分析"
else
    echo "ℹ️  今天没有高价值发现，明天继续搜索"
fi

echo ""
echo "✅ 每日分析完成"
