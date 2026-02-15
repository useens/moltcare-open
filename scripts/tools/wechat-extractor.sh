#!/bin/bash
# wechat-extractor.sh - 微信公众号文章提取工具
# 用途: 绕过反爬机制，提取公众号文章纯文本内容
# 限制: 微信可能随时更新反爬机制，此方法不保证长期有效

set -e

if [ $# -lt 1 ]; then
    echo "用法: $0 <微信公众号文章URL> [输出文件]"
    echo ""
    echo "示例:"
    echo "  $0 'https://mp.weixin.qq.com/s/xxxxx'"
    echo "  $0 'https://mp.weixin.qq.com/s/xxxxx' article.txt >> learning-debt.md"
    echo ""
    echo "原理:"
    echo "  1. 模拟iPhone移动端UA绕过部分反爬"
    echo "  2. 提取rich_media_content区块"
    echo "  3. 去除HTML标签，保留纯文本"
    exit 1
fi

URL="$1"
OUTPUT_FILE="${2:-}"
UA="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"

echo "🔍 提取: $URL" >&2

# 核心提取逻辑
# 注意: 微信HTML结构可能变化，如失效需更新选择器
HTML=$(curl -s -L "$URL" -A "$UA" --max-time 15 2>/dev/null)

if [ -z "$HTML" ]; then
    echo "❌ 无法获取页面" >&2
    exit 1
fi

# 提取并清理内容
# 方法: 找到js_content div，提取到下一个/div为止
CONTENT=$(echo "$HTML" | \
    grep -oP '(?<=id="js_content")[^>]*>\K.*?(?=</div>)' | \
    head -1 | \
    sed 's/<[^\u003e]*>/ /g' | \
    sed 's/&nbsp;/ /g; s/&amp;/\&/g' | \
    tr -s ' ')

if [ ${#CONTENT} -lt 100 ]; then
    echo "⚠️ 提取内容较短，建议手动检查" >&2
fi

# 输出
if [ -n "$OUTPUT_FILE" ]; then
    echo "$CONTENT" > "$OUTPUT_FILE"
    echo "✅ 已保存 (${#CONTENT} 字符): $OUTPUT_FILE" >&2
else
    echo "$CONTENT"
fi
