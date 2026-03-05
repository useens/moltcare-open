#!/bin/bash
# 部署Nanobot V2到所有小弟

echo "======================================================================"
echo "🚀 部署Nanobot V2 - 具备执行能力"
echo "======================================================================"
echo ""

# 停止旧版本
echo "1. 停止旧版本..."
pkill -f "simple_nanobot" 2>/dev/null
sleep 2
echo "   ✅ 已停止"
echo ""

# 创建workspace目录
mkdir -p /root/.openclaw/workspace/nanobot-workspace
echo "2. 创建工作目录..."
for i in {1..10}; do
    mkdir -p /root/.openclaw/workspace/nanobot-workspace/nanobot-${i}
done
echo "   ✅ 已创建"
echo ""

# 启动V2版本
echo "3. 启动V2版本..."
cd /root/.openclaw/workspace/ai-nanobots

for i in {1..10}; do
    NB="nanobot-${i}"
    nohup python3 nanobot_v2.py "${NB}" > "${NB}.log" 2>&1 &
    echo "   ✅ ${NB} V2 启动"
    sleep 0.5
done

echo ""
echo "等待启动..."
sleep 5

echo ""
echo "4. 检查状态:"
COUNT=$(ps aux | grep "nanobot_v2" | grep -v grep | wc -l)
echo "   ${COUNT}/10 个V2进程运行中"

echo ""
echo "======================================================================"
echo "✅ Nanobot V2 部署完成！"
echo "======================================================================"
echo ""
echo "新能力："
echo "  🛠️ exec - 执行系统命令 (ls, cat, python3...)"
echo "  📄 read - 读取文件"
echo "  ✏️  write - 写入文件"
echo "  🌐 web_fetch - 获取网页"
echo ""
echo "安全限制："
echo "  • 禁止危险命令 (rm -rf /, mkfs等)"
echo "  • 只能操作工作目录内的文件"
echo "  • 命令执行超时30秒"
echo ""
echo "测试命令："
echo "  '列出当前目录'"
echo "  '读取 /path/to/file'"
echo "  '执行 python3 --version'"
echo "======================================================================"
