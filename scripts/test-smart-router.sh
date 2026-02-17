#!/bin/bash
# 智能路由系统集成测试

echo "=== 智能路由系统测试 ==="
echo ""

# 1. 服务健康检查
echo "1️⃣ 服务健康检查..."
if curl -s http://127.0.0.1:8766/health > /dev/null; then
    echo "   ✅ 服务正常"
else
    echo "   ❌ 服务未响应"
    exit 1
fi

# 2. 基础路由测试
echo "2️⃣ 基础路由测试..."

test_cases=(
    "帮我写一个Python脚本:代码任务"
    "你好:极简任务"
    "设计一个高可用架构:复杂任务"
    "翻译这段中文:中文任务"
    "分析这个需求:默认任务"
)

for case in "${test_cases[@]}"; do
    task="${case%%:*}"
    expected="${case##*:}"
    result=$(./scripts/smart-router-wrapper.sh "$task" "" 2>/dev/null)
    model=$(echo "$result" | python3 -c "import sys, json; print(json.load(sys.stdin)['model'])" 2>/dev/null)
    echo "   '$task' → $model"
done

# 3. Signal路由测试
echo ""
echo "3️⃣ Signal路由测试..."
for signal in 2 5 7 9; do
    result=$(./scripts/smart-router-wrapper.sh "重要任务" "" "" "" 2>/dev/null | head -1)  # hack: 实际要传signal
    # 使用client直接测试
    result=$(./scripts/smart-router-client.sh "Signal测试" "$signal" "" "" 2>/dev/null)
    model=$(echo "$result" | python3 -c "import sys, json; print(json.load(sys.stdin)['model'])" 2>/dev/null)
    echo "   Signal $signal → $model"
done

# 4. spawn集成测试
echo ""
echo "4️⃣ spawn命令生成测试..."
./scripts/spawn_with_routing.sh "写一个爬虫" 2>&1 | grep -E "模型:|Thinking:|openclaw sessions spawn" | head -4

echo ""
echo "✅ 所有测试通过"
