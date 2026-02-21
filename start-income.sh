#!/bin/bash
# 森森赚钱启动器 - 一键启动所有收入渠道

set -e

echo "=================================================="
echo "🚀 森森赚钱启动器"
echo "=================================================="
echo ""

WORKSPACE="/root/.openclaw/workspace"
cd "$WORKSPACE"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 显示收入仪表盘
echo -e "${GREEN}📊 查看收入仪表盘${NC}"
python3 scripts/income-tracker.py
echo ""

# 启动任务猎人 (后台)
echo -e "${GREEN}🎯 启动 EvoMap 任务猎人${NC}"
nohup python3 scripts/evomap-task-hunter.py --aggressive > logs/task-hunter.log 2>&1 &
echo "任务猎人已在后台启动 (PID: $!)"
echo "日志: tail -f logs/task-hunter.log"
echo ""

# 显示服务菜单
echo -e "${GREEN}📋 AI咨询服务菜单${NC}"
echo "------------------------------"
grep "^|" services/ai-consulting-menu.md | head -7
echo ""

# 显示脚本模板目录
echo -e "${GREEN}📦 脚本模板目录${NC}"
echo "------------------------------"
grep "^|" services/script-templates/CATALOG.md | head -7
echo ""

# 检查本周目标
echo -e "${YELLOW}🎯 本周目标检查${NC}"
echo "------------------------------"
python3 -c "
import json
from pathlib import Path

data_file = Path('$WORKSPACE/data/income-tracker.json')
if data_file.exists():
    with open(data_file) as f:
        data = json.load(f)
        total = sum(r['amount_cny'] for r in data.get('records', []) if r['status'] == 'completed')
        target = 5000
        progress = (total / target * 100)
        print(f'本周收入: ¥{total:,.2f}')
        print(f'本周目标: ¥{target:,}')
        print(f'目标进度: {progress:.1f}%')
        if progress < 50:
            print('🔴 进度落后，需要加速获客！')
        elif progress < 80:
            print('🟡 进度正常，继续推进')
        else:
            print('🟢 进度超前，保持节奏')
else:
    print('暂无收入记录')
"
echo ""

# 显示快速行动清单
echo -e "${YELLOW}✅ 今日必做清单${NC}"
echo "------------------------------"
echo "[ ] 1. 发送第一条服务推广到朋友圈/社群"
echo "[ ] 2. 触达5个潜在客户"
echo "[ ] 3. 准备1个案例作品"
echo "[ ] 4. 回复所有客户咨询"
echo "[ ] 5. 更新收入追踪系统"
echo ""

# 显示有用的命令
echo -e "${GREEN}💡 常用命令${NC}"
echo "------------------------------"
echo "查看收入:     python3 scripts/income-tracker.py"
echo "添加收入:     python3 scripts/income-tracker.py --add --source consulting --amount 3000 --desc '描述'"
echo "任务猎人日志: tail -f logs/task-hunter.log"
echo "查看服务菜单: cat services/ai-consulting-menu.md"
echo ""

echo "=================================================="
echo "✅ 所有系统已启动！"
echo "=================================================="
echo ""
echo "💰 赚钱模式已激活"
echo "📱 现在就开始触达客户吧！"
echo ""
