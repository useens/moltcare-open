#!/bin/bash
# 测试10个Nanobot节点的实际对话功能

BASE_URL="https://integrate.api.nvidia.com/v1"
MODEL="z-ai/glm4.7"
API_KEYS=(
  "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"
  "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"
  "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"
  "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"
  "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"
  "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"
  "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"
  "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"
  "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"
  "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"
)

echo "测试10个Nanobot节点对话功能..."
echo "================================"

for i in {0..9}; do
  NODE_NUM=$((i+1))
  API_KEY="${API_KEYS[$i]}"
  TEST_MSG="Test from node $NODE_NUM"
  
  printf "NB%02d: " $NODE_NUM
  
  RESPONSE=$(curl -s -w "\n%{http_code}" \
    --max-time 30 \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"$MODEL\", \"messages\": [{\"role\": \"user\", \"content\": \"$TEST_MSG\"}], \"max_tokens\": 20}" \
    "$BASE_URL/chat/completions" 2>/dev/null)
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | head -n -1)
  
  if [ "$HTTP_CODE" = "200" ]; then
    CONTENT=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])" 2>/dev/null)
    if [ -n "$CONTENT" ]; then
      echo "✅ 响应正常"
    else
      echo "🟡 响应为空"
    fi
  elif [ "$HTTP_CODE" = "401" ]; then
    echo "❌ 认证失败"
  elif [ "$HTTP_CODE" = "429" ]; then
    echo "⚠️  速率限制"
  else
    echo "❌ 错误 HTTP $HTTP_CODE"
  fi
done

echo "================================"
echo "测试完成"
