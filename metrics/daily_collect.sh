#!/bin/bash
# 每日指标自动收集
# 由Cron定时调用

echo "📊 $(date '+%Y-%m-%d %H:%M') 收集每日指标..."

cd /root/.openclaw/workspace

# 1. 统计债务数据
echo "  统计债务数据..."
SIGNAL10=$(grep -c "Signal 10/10" memory/learning-debt.md 2>/dev/null || echo 0)
SIGNAL10_DONE=$(grep -c "Signal 10/10.*✅" memory/learning-debt.md 2>/dev/null || echo 0)

# 2. 统计Cron成功率
echo "  统计Cron成功率..."
CRON_RUNS=$(python3 -c "
import json
import subprocess
result = subprocess.run(['openclaw', 'cron', 'runs', '--job', '918f740f-5375-49c9-823c-2eb284353b1c', '--limit', '20', '--json'], capture_output=True, text=True)
if result.returncode == 0:
    data = json.loads(result.stdout)
    runs = data.get('entries', [])
    total = len(runs)
    success = sum(1 for r in runs if r.get('status') == 'ok')
    print(f'{success}/{total}')
else:
    print('N/A')
" 2>/dev/null || echo "N/A")

# 3. 更新指标
echo "  更新指标..."
python3 << EOF
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
from metrics.engine import MetricsEngine

engine = MetricsEngine()

# 更新债务处理速度
engine.update_metric("execution", "debt_processing_velocity", ${SIGNAL10_DONE:-0}, "今日处理${SIGNAL10_DONE}条Signal 10债务")

print("✅ 指标已更新")
EOF

# 4. 生成报告
echo "  生成每日报告..."
python3 -c "
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
from metrics.engine import MetricsEngine
engine = MetricsEngine()
engine.generate_daily_report()
" 

echo "✅ 每日指标收集完成"
