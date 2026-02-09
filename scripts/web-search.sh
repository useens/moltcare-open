#!/bin/bash
# web-search.sh - 命令行网络搜索工具
# 使用 ddgr (DuckDuckGo) 无需 API key

search_web() {
    local query="$1"
    local limit="${2:-5}"
    
    echo "🔍 搜索: $query"
    echo ""
    
    # 使用 ddgr 搜索
    ddgr -n "$limit" --np "$query" 2>/dev/null || {
        echo "搜索失败，尝试备用方法..."
        # 备用：使用 curl + duckduckgo html
        curl -s "https://html.duckduckgo.com/html/?q=$(echo "$query" | sed 's/ /+/g')" \
            -H "User-Agent: Mozilla/5.0" 2>/dev/null | \
            grep -oP 'class="result__a"[^>]*href="[^"]*"[^>]*>[^<]*</a>' | \
            head -$limit | \
            sed 's/.*href="//;s/".*>/ | /;s/<\/a>//' || \
            echo "搜索服务暂时不可用"
    }
}

# 如果直接运行
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    if [ $# -eq 0 ]; then
        echo "用法: web-search.sh \"搜索关键词\" [结果数量]"
        exit 1
    fi
    search_web "$1" "${2:-5}"
fi
