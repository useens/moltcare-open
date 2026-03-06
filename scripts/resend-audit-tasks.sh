#!/bin/bash
# 重新发送脚本审计任务 - 使用正确的格式

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
TASKS_FILE=$HUB_DIR/tasks.jsonl
TIMESTAMP=$(date -Iseconds)

echo "🔄 重新发送脚本审计任务"
echo "======================="

# nanobot-1 研究员: Moltbook脚本分析
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-1","data":{"description":"深度审计Moltbook相关Python脚本。\n\n任务:\n1. 分析所有moltbook*.py脚本的功能\n2. 识别版本重复(v7-v71共17个版本)\n3. 推荐保留哪些版本(建议保留v60,v61,v71)\n4. 列出可安全删除的脚本\n\n注意:\n- 使用exec工具执行ls和grep命令\n- 使用read工具读取脚本内容分析\n- 输出JSON格式的审计报告\n\n输出保存到: /root/.openclaw/workspace/reports/nanobot-1-moltbook-audit.json","priority":"high","context":"research"},"timestamp":"$TIMESTAMP"}
EOF

# nanobot-4 安全专家: 识别临时脚本
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-4","data":{"description":"识别可删除的临时/测试脚本。\n\n任务:\n1. 扫描所有fix*.py和verify*.py脚本\n2. 检查这些脚本是否还在被使用\n3. 分析test*.py脚本是否可以归档\n4. 检查capability-breakthrough-exp-*.py实验脚本\n\n注意:\n- 检查脚本内容判断是否为临时修复\n- 确认没有cron或进程依赖后再标记为可删除\n- 输出JSON格式的安全删除清单\n\n输出保存到: /root/.openclaw/workspace/reports/nanobot-4-security-audit.json","priority":"high","context":"security"},"timestamp":"$TIMESTAMP"}
EOF

# nanobot-7 代码审查员: 版本重复检测
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-7","data":{"description":"检测脚本版本重复和代码重复。\n\n任务:\n1. 分析所有*_v*.py脚本的版本演进\n2. 识别功能重复的脚本对\n3. 比较相似脚本的内容差异\n4. 推荐合并方案\n\n重点检查:\n- token_optimizer_v10.py vs token-optimizer-v10.py\n- state-snapshot-drift*.py的多个版本\n- moltbook_social_v*.py的版本链\n\n输出保存到: /root/.openclaw/workspace/reports/nanobot-7-version-audit.json","priority":"high","context":"code_review"},"timestamp":"$TIMESTAMP"}
EOF

# nanobot-8 运维专家: 活跃状态分析
cat >> $TASKS_FILE << EOF
{"type":"task","agent_id":"nanobot-8","data":{"description":"分析316个脚本的活跃状态和依赖关系。\n\n任务:\n1. 使用exec执行: find /root/.openclaw/workspace/scripts -name '*.py' -type f -atime -30 | wc -l\n2. 检查crontab中引用的脚本\n3. 检查运行中的进程使用的脚本\n4. 生成活跃脚本白名单\n\n注意:\n- 使用exec工具执行系统命令\n- 不要调用LLM API(会返回403错误)\n- 直接执行命令获取真实数据\n\n输出保存到: /root/.openclaw/workspace/reports/nanobot-8-activity-audit.json","priority":"high","context":"ops"},"timestamp":"$TIMESTAMP"}
EOF

echo "✅ 已重新发送4个审计任务"
echo ""
echo "任务队列最新4条:"
tail -4 $TASKS_FILE
echo ""
echo "等待Agent处理 (约需2-3分钟)..."
