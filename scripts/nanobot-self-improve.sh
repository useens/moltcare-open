#!/bin/bash
# 让所有Nanobot小弟自行优化改进

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
TASKS_FILE=$HUB_DIR/tasks.jsonl
TIMESTAMP=$(date -Iseconds)

echo "🎯 通知所有小弟：自行优化改进"
echo "==============================="
echo ""

# 清空旧结果
echo "" > $HUB_DIR/results.jsonl

echo "向所有10个小弟发送自我优化任务..."
echo ""

# 给所有10个小弟发送自我优化任务
for i in $(seq 1 10); do
    ROLE=$(cat /root/.openclaw/workspace/projects/nanobot/agents/nanobot-${i}/identity.json 2>/dev/null | grep '"role"' | cut -d'"' -f4)
    
    cat >> $TASKS_FILE <> $HUB_DIR/results.jsonl 2>/dev/null | wc -l
echo "  个小弟已回复"
echo ""

echo "📊 各小弟的自我优化建议:"
cat $HUB_DIR/results.jsonl | python3 -c "
import sys, json

roles = {
    'nanobot-1': '研究员',
    'nanobot-2': '架构师', 
    'nanobot-3': '工程师',
    'nanobot-4': '安全专家',
    'nanobot-5': '分析师',
    'nanobot-6': '决策分析师',
    'nanobot-7': '代码审查员',
    'nanobot-8': '运维专家',
    'nanobot-9': '战略规划师',
    'nanobot-10': '协调者'
}

seen = set()
for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        agent = d['agent_id']
        if agent in seen:
            continue
        seen.add(agent)
        
        role = roles.get(agent, '未知')
        result = d['result']['result']
        
        # 提取建议
        import re
        suggestions = re.findall(r'\d+\.\s*([^\n]+)', result)
        
        print(f'🤖 {agent} ({role})')
        if suggestions:
            for s in suggestions[:3]:
                print(f'   💡 {s[:60]}')
        else:
            preview = result.replace('\n', ' ')[:70]
            print(f'   📝 {preview}...')
        print()
    except:
        pass
"

echo "✅ 自我优化任务已分发完成"
echo ""
echo "📝 说明：每个小弟都收到了自我分析和改进的任务"
echo "   他们将基于自己的角色和近期表现提出优化建议"
