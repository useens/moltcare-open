#!/bin/bash
# 给四个Nanobot小弟布置复杂任务

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
TASKS_FILE=$HUB_DIR/tasks.jsonl
TIMESTAMP=$(date -Iseconds)

echo "🎯 给四个Nanobot小弟布置复杂任务"
echo "================================="
echo ""

# 清空旧结果
echo "" > $HUB_DIR/results.jsonl

# 小弟1: nanobot-1 研究员 - 系统全面分析
cat >> $TASKS_FILE <> $HUB_DIR/results.jsonl 2>/dev/null | wc -l
echo "  个任务已完成"
echo ""

echo "4️⃣ 各小弟成果摘要:"
tail -4 $HUB_DIR/results.jsonl 2>/dev/null | while read line; do
    echo "$line" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    agent = d['agent_id']
    role = agent.replace('nanobot-', '小弟')
    cmds = d['result'].get('commands_count', 0)
    result = d['result']['result']
    
    # 提取关键信息
    if '执行成功' in result:
        status = '✅ 成功'
    elif '执行失败' in result:
        status = '❌ 失败'
    else:
        status = '⚠️ 未知'
    
    # 提取数字
    import re
    numbers = re.findall(r'\d+', result)
    summary = f'发现 {len(numbers)} 个数据点' if numbers else '完成分析'
    
    print(f\"{role} ({agent}): {status} - 执行了{cmds}个命令 - {summary}\")
except:
    pass
" 2>/dev/null
done

echo ""
echo "5️⃣ 查看详细结果:"
for i in 1 4 7 8; do
    log_file="/root/.openclaw/workspace/projects/nanobot/logs/nanobot-${i}.log"
    echo "nanobot-${i} 最近日志:"
    tail -3 "$log_file" 2>/dev/null | sed 's/^/  /'
    echo ""
done

echo "✅ 复杂任务测试完成"
