#!/bin/bash
# 重新发送脚本审计任务给Nanobot - 使用正确的tasks.jsonl格式

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
TASKS_FILE=$HUB_DIR/tasks.jsonl
TIMESTAMP=$(date -Iseconds)

echo "🤖 重新发送脚本审计任务给Nanobot"
echo "================================"
echo ""

# 清空旧的任务结果
echo "清理旧的任务结果..."
echo "" > $HUB_DIR/results.jsonl
echo "✅ 已清空 results.jsonl"
echo ""

# 写入4个审计任务到tasks.jsonl
echo "发送任务到tasks.jsonl..."

# nanobot-1 研究员: Moltbook脚本分析
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-1","data":{"description":"深度审计Moltbook相关Python脚本。\n\n任务:\n1. 使用exec工具执行: ls -la /root/.openclaw/workspace/scripts/moltbook*.py | wc -l\n2. 分析所有moltbook*.py脚本的功能\n3. 识别版本重复(v7-v71共17个版本)\n4. 推荐保留哪些版本(建议保留v60,v61,v71)\n5. 列出可安全删除的脚本\n\n注意:\n- 使用exec工具执行系统命令获取数据\n- 使用read工具读取脚本内容分析\n- 输出JSON格式的审计报告\n\n输出保存到: /root/.openclaw/workspace/reports/nanobot-1-moltbook-audit.json","priority":"high","context":"research"},"timestamp":"$TIMESTAMP"}
EOF

# nanobot-4 安全专家: 识别临时脚本
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-4","data":{"description":"识别可删除的临时/测试脚本。\n\n任务:\n1. 使用exec执行: ls /root/.openclaw/workspace/scripts/fix*.py /root/.openclaw/workspace/scripts/verify*.py 2>/dev/null\n2. 使用exec执行: ls /root/.openclaw/workspace/scripts/test*.py 2>/dev/null\n3. 使用exec执行: ls /root/.openclaw/workspace/scripts/capability-breakthrough-exp-*.py 2>/dev/null\n4. 检查这些脚本是否还在被使用\n5. 输出JSON格式的安全删除清单\n\n注意:\n- 使用exec工具执行系统命令\n- 不要调用LLM API，直接使用系统命令\n\n输出保存到: /root/.openclaw/workspace/reports/nanobot-4-security-audit.json","priority":"high","context":"security"},"timestamp":"$TIMESTAMP"}
EOF

# nanobot-7 代码审查员: 版本重复检测
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-7","data":{"description":"检测脚本版本重复和代码重复。\n\n任务:\n1. 使用exec执行: ls /root/.openclaw/workspace/scripts/*_v*.py 2>/dev/null | wc -l\n2. 识别功能重复的脚本对\n3. 重点检查重复命名:\n   - token_optimizer_v10.py vs token-optimizer-v10.py\n   - state-snapshot-drift*.py的多个版本\n4. 输出重复脚本清单\n\n注意:\n- 使用exec工具执行系统命令\n- 不要调用LLM API\n\n输出保存到: /root/.openclaw/workspace/reports/nanobot-7-version-audit.json","priority":"high","context":"code_review"},"timestamp":"$TIMESTAMP"}
EOF

# nanobot-8 运维专家: 活跃状态分析
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-8","data":{"description":"分析316个脚本的活跃状态和依赖关系。\n\n任务:\n1. 使用exec执行: find /root/.openclaw/workspace/scripts -name '*.py' -type f | wc -l\n2. 使用exec执行: find /root/.openclaw/workspace/scripts -name '*.py' -type f -atime -30 | wc -l\n3. 使用exec执行: crontab -l | grep -c 'py'\n4. 使用exec执行: ps aux | grep python | grep -v grep | wc -l\n5. 生成活跃脚本报告\n\n注意:\n- 全部使用exec工具执行系统命令\n- 不要调用LLM API\n- 直接获取真实数据\n\n输出保存到: /root/.openclaw/workspace/reports/nanobot-8-activity-audit.json","priority":"high","context":"ops"},"timestamp":"$TIMESTAMP"}
EOF

echo "✅ 已发送4个审计任务到 tasks.jsonl"
echo ""
echo "任务队列:"
tail -4 $TASKS_FILE | python3 -m json.tool 2>/dev/null | grep '"agent_id"' | sed 's/^/  /'
echo ""

# 检查Agent状态
echo "Agent进程状态:"
ps aux | grep "agent.py nanobot" | grep -v grep | wc -l
echo "  个Agent运行中"
echo ""

echo "⏳ 等待Agent处理任务 (约需1-2分钟)..."
echo "提示: Agent每3秒检查一次任务队列"
