#!/bin/bash
# 316脚本审计任务分派
# 神经中枢 → 多Agent并行分析

HUB_DIR=/root/.openclaw/workspace/projects/nanobot/hub
timestamp=$(date -Iseconds)

echo "🤖 启动脚本审计任务分派"
echo "========================"

# 创建分析任务给多个Agent

# nanobot-1 研究员: 分析Moltbook相关脚本
mkdir -p $HUB_DIR/inbox
cat > $HUB_DIR/inbox/nanobot-1_script_audit.json << 'EOF'
{
  "id": "audit_moltbook_$(date +%s)",
  "agent": "nanobot-1",
  "type": "script_audit",
  "category": "moltbook",
  "description": "审计所有Moltbook相关脚本，识别有用/无用/可删除",
  "priority": "high",
  "created_at": "$(date -Iseconds)",
  "task": {
    "pattern": "moltbook*",
    "count": 80,
    "criteria": ["最近使用", "是否有用", "是否重复版本", "是否可删除"],
    "output_file": "/root/.openclaw/workspace/reports/script-audit-moltbot.json"
  }
}
EOF

# nanobot-4 安全专家: 识别临时脚本和测试脚本
cat > $HUB_DIR/inbox/nanobot-4_script_audit.json << 'EOF'
{
  "id": "audit_temp_$(date +%s)",
  "agent": "nanobot-4",
  "type": "script_audit",
  "category": "temp_test",
  "description": "识别临时修复脚本、测试脚本、安全相关脚本",
  "priority": "high",
  "created_at": "$(date -Iseconds)",
  "task": {
    "patterns": ["test_*.py", "fix_*.py", "*test*.py", "*fix*.py", "verify*.py"],
    "criteria": ["是否临时", "是否测试", "是否安全关键", "是否可删除"],
    "output_file": "/root/.openclaw/workspace/reports/script-audit-temp.json"
  }
}
EOF

# nanobot-7 代码审查员: 识别重复和版本脚本
cat > $HUB_DIR/inbox/nanobot-7_script_audit.json << 'EOF'
{
  "id": "audit_versions_$(date +%s)",
  "agent": "nanobot-7",
  "type": "script_audit",
  "category": "versions",
  "description": "识别多版本脚本(v1,v2...v60)和重复脚本，推荐保留版本",
  "priority": "high",
  "created_at": "$(date -Iseconds)",
  "task": {
    "patterns": ["*_v*.py", "*v[0-9]*.py", "capability-breakthrough-exp-*.py"],
    "criteria": ["版本号分析", "最新版本识别", "旧版本可删除性", "重复代码检测"],
    "output_file": "/root/.openclaw/workspace/reports/script-audit-versions.json"
  }
}
EOF

# nanobot-8 运维专家: 识别活跃vs废弃脚本
cat > $HUB_DIR/inbox/nanobot-8_script_audit.json << 'EOF'
{
  "id": "audit_active_$(date +%s)",
  "agent": "nanobot-8",
  "type": "script_audit",
  "category": "activity",
  "description": "基于文件访问时间和cron配置，识别活跃/废弃脚本",
  "priority": "high",
  "created_at": "$(date -Iseconds)",
  "task": {
    "criteria": ["30天内访问", "cron中引用", "daemon运行", "依赖关系"],
    "check_cron": true,
    "check_processes": true,
    "output_file": "/root/.openclaw/workspace/reports/script-audit-activity.json"
  }
}
EOF

echo "✅ 已分派4个审计任务:"
echo "  - nanobot-1: Moltbook脚本分析"
echo "  - nanobot-4: 临时/测试脚本识别"
echo "  - nanobot-7: 版本重复检测"
echo "  - nanobot-8: 活跃状态分析"
echo ""
echo "📊 任务队列: $HUB_DIR/inbox/"
ls $HUB_DIR/inbox/*.json 2>/dev/null | wc -l
echo "  个任务待处理"
