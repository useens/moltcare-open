#!/bin/bash
# 发送全面脚本审计任务给Nanobot
# 审计范围：所有scripts目录下的脚本

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
TASKS_FILE=$HUB_DIR/tasks.jsonl
TIMESTAMP=$(date -Iseconds)

echo "🤖 发送全面脚本审计任务"
echo "======================="
echo ""

# 清空旧结果
echo "" > $HUB_DIR/results.jsonl

# 任务1: nanobot-1 研究员 - 全面脚本清单
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-1","data":{"description":"全面审计脚本 - 生成完整清单。\n\n执行以下命令并分析结果:\n1. find /root/.openclaw/workspace/scripts -name '*.py' -type f | wc -l\n2. find /root/.openclaw/workspace/scripts -name '*.sh' -type f | wc -l\n3. ls -la /root/.openclaw/workspace/scripts/*.py | head -20\n4. find /root/.openclaw/workspace/scripts -name '*.py' -type f -atime -30 | wc -l\n\n生成报告:/root/.openclaw/workspace/reports/nanobot-audit-full-inventory.json","priority":"high","context":"research"},"timestamp":"$TIMESTAMP"}
EOF

# 任务2: nanobot-4 安全专家 - 识别废弃脚本
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-4","data":{"description":"安全审计 - 识别可删除脚本。\n\n执行以下命令:\n1. find /root/.openclaw/workspace/scripts/.archive -name '*.py' 2>/dev/null | wc -l\n2. ls /root/.openclaw/workspace/scripts/tests/*.py 2>/dev/null | wc -l\n3. crontab -l 2>/dev/null | grep -oE '[a-zA-Z0-9_-]+\.(py|sh)' | sort -u\n4. ps aux | grep python | grep -v grep | awk '{print \$NF}' | sort -u | head -20\n\n分析哪些脚本在cron或进程中使用，哪些未使用。\n\n报告:/root/.openclaw/workspace/reports/nanobot-audit-unused.json","priority":"high","context":"security"},"timestamp":"$TIMESTAMP"}
EOF

# 任务3: nanobot-7 代码审查员 - 质量分析
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-7","data":{"description":"代码质量审计 - 分析脚本质量。\n\n执行:\n1. 统计scripts目录总行数: find /root/.openclaw/workspace/scripts -name '*.py' -exec wc -l {} + | tail -1\n2. 找出最大脚本: ls -lS /root/.openclaw/workspace/scripts/*.py | head -10\n3. 检查是否有空文件: find /root/.openclaw/workspace/scripts -name '*.py' -size 0\n4. 统计重复文件名(不同目录): find /root/.openclaw/workspace/scripts -name '*.py' | xargs basename -a | sort | uniq -c | sort -rn | head -10\n\n报告:/root/.openclaw/workspace/reports/nanobot-audit-quality.json","priority":"high","context":"code_review"},"timestamp":"$TIMESTAMP"}
EOF

# 任务4: nanobot-8 运维专家 - 系统依赖分析
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-8","data":{"description":"运维审计 - 系统依赖分析。\n\n执行:\n1. 检查脚本导入关系: grep -r '^import\|^from' /root/.openclaw/workspace/scripts/*.py 2>/dev/null | grep -v '.pyc' | wc -l\n2. 找出被导入最多的模块: grep -r '^import\|^from' /root/.openclaw/workspace/scripts/*.py 2>/dev/null | sed 's/.*import //' | sort | uniq -c | sort -rn | head -20\n3. 检查脚本之间的相互导入: grep -r 'from.*scripts' /root/.openclaw/workspace/scripts/*.py 2>/dev/null | head -20\n4. df -h /root/.openclaw/workspace\n\n报告:/root/.openclaw/workspace/reports/nanobot-audit-dependencies.json","priority":"high","context":"ops"},"timestamp":"$TIMESTAMP"}
EOF

echo "✅ 已发送4个全面审计任务"
echo ""
echo "任务列表:"
grep '"agent_id"' $TASKS_FILE | tail -4 | sed 's/^/  /'
echo ""
echo "⏳ 等待处理 (约1-2分钟)..."
