#!/bin/bash
# Agent Reach 服务监控脚本

echo "=== Agent Reach 服务监控 $(date) ==="

# 检查并重启停止的服务
check_service() {
    local name=$1
    local port=$2
    local check_url=$3
    
    if ! curl -s "$check_url" > /dev/null 2>&1; then
        echo "⚠️ $name 服务未运行，尝试重启..."
        return 1
    fi
    echo "✅ $name 运行正常"
    return 0
}

# 检查抖音
check_service "抖音" 18070 "http://localhost:18070/mcp" || {
    cd ~/.agent-reach/tools/douyin-mcp-server 2>/dev/null && \
    nohup ~/.agent-reach/venv/bin/python -c "
from douyin_mcp_server.server import mcp
mcp.settings.host = '127.0.0.1'
mcp.settings.port = 18070
mcp.run(transport='streamable-http')
" > /tmp/douyin.log 2>&1 &
    sleep 2
    echo "抖音服务已重启"
}

# 检查 Boss直聘
check_service "Boss直聘" 8000 "http://localhost:8000/mcp" || {
    cd ~/.agent-reach/tools/mcp-bosszp && \
    nohup ~/.agent-reach/venv/bin/python boss_zhipin_fastmcp_v2.py > /tmp/bosszp.log 2>&1 &
    sleep 2
    echo "Boss直聘服务已重启"
}

# 检查小红书
check_service "小红书" 18060 "http://localhost:18060/mcp" || {
    docker start xiaohongshu-mcp 2>/dev/null || echo "小红书 Docker 需要手动重启"
}

echo "=== 监控完成 ==="
