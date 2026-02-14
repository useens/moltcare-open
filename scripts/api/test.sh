#!/bin/bash
# HTTP API通信测试脚本

set -e

PRIMARY_URL=${PRIMARY_URL:-"http://localhost:2346"}
TOKEN=${SENSEN_API_TOKEN:-"default-token"}

echo "═══════════════════════════════════════════════════════════"
echo "  🌲 Sensen API 通信测试"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Primary URL: $PRIMARY_URL"
echo "Token: ${TOKEN:0:10}..."
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $method $endpoint ... "
    
    response=$(curl -s -w "\n%{http_code}" \
        -X "$method" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        "$PRIMARY_URL$endpoint" 2>/dev/null || echo -e "\n000")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}OK${NC} ($http_code)"
        return 0
    else
        echo -e "${RED}FAIL${NC} (expected $expected_code, got $http_code)"
        echo "  Response: $body"
        return 1
    fi
}

echo "1. 健康检查 (无需认证)"
curl -sf "$PRIMARY_URL/health" > /dev/null && echo -e "  ${GREEN}OK${NC}" || echo -e "  ${RED}FAIL${NC}"

echo ""
echo "2. API端点测试"
test_endpoint "GET" "/"
test_endpoint "GET" "/api/tasks/pending"
test_endpoint "GET" "/api/nodes/primary/status"

echo ""
echo "3. 创建测试任务"
task_response=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"type": "test", "priority": "normal", "payload": {"test": true}}' \
    "$PRIMARY_URL/api/tasks")

echo "  Task created: $task_response"
task_id=$(echo "$task_response" | grep -o '"task_id": "[^"]*"' | cut -d'"' -f4)

echo ""
echo "4. 查询任务列表"
test_endpoint "GET" "/api/tasks/list"

echo ""
echo "5. 清理测试任务"
if [ -n "$task_id" ]; then
    curl -s -X POST \
        -H "Authorization: Bearer $TOKEN" \
        "$PRIMARY_URL/api/tasks/cleanup" > /dev/null
    echo "  Cleanup done"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "测试完成"
echo "═══════════════════════════════════════════════════════════"
