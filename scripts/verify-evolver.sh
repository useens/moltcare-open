#!/bin/bash
# Evolver & EvoMap 完整验证脚本
# 验证所有组件正常工作

echo "🔍 运行完整验证..."
echo ""

cd /root/.openclaw/workspace

# 1. 验证 index.js env 路径
echo "=== 1. index.js env 路径检查 ==="
if grep -q "path.resolve(__dirname, '.env')" evolver/index.js; then
    echo "✅ index.js env 路径已修复为 ./.env"
else
    echo "❌ index.js env 路径未修复"
    exit 1
fi

# 2. 验证 a2aProtocol.js
echo ""
echo "=== 2. a2aProtocol.js 检查 ==="
if grep -q "EVOLVER_NODE_ID" evolver/src/gep/a2aProtocol.js; then
    echo "✅ a2aProtocol.js 已添加 EVOLVER_NODE_ID 支持"
else
    echo "❌ a2aProtocol.js 未修复"
    exit 1
fi

# 3. 验证节点 ID
echo ""
echo "=== 3. 节点 ID 验证 ==="
NODE_ID=$(cd evolver && node -e "
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '.env') });
const { getNodeId } = require('./src/gep/a2aProtocol');
console.log(getNodeId());
" 2>/dev/null | tail -1)

if [ "$NODE_ID" = "node_e8d73f59" ]; then
    echo "✅ 节点 ID 正确: $NODE_ID"
else
    echo "❌ 节点 ID 错误: $NODE_ID (应为 node_e8d73f59)"
    exit 1
fi

# 4. 验证 EvoMap 连接
echo ""
echo "=== 4. EvoMap 连接验证 ==="
python3 -c "
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
from scripts.evomap.client import EvoMapClient
from scripts.evomap.config import EvoMapConfig

config = EvoMapConfig.load()
client = EvoMapClient(config)
result = client.fetch(include_tasks=True)
tasks = result.get('payload', {}).get('tasks', [])
print(f'✅ 成功获取 {len(tasks)} 个任务')
" || exit 1

# 5. 验证 Evolver 任务获取
echo ""
echo "=== 5. Evolver 任务获取验证 ==="
cd evolver && node -e "
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '.env') });
const { fetchTasks } = require('./src/gep/taskReceiver');
fetchTasks().then(tasks => {
    console.log('✅ Evolver 成功获取 ' + tasks.length + ' 个任务');
}).catch(err => {
    console.error('❌ 失败:', err.message);
    process.exit(1);
});
"

echo ""
echo "==================================="
echo "✅ 所有验证通过！"
echo "==================================="
