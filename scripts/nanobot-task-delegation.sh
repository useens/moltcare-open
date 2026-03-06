#!/bin/bash
# nanobot-task-delegation.sh
# 精简模式下任务移交脚本
# 创建时间: 2026-03-06

WORKSPACE=/root/.openclaw/workspace
NANOBOT_DIR=$WORKSPACE/projects/nanobot
HUB_DIR=$NANOBOT_DIR/hub

echo "🤖 精简模式任务移交启动"
echo "========================"

# 确保hub目录存在
mkdir -p $HUB_DIR/inbox $HUB_DIR/outbox $HUB_DIR/logs

# ============================================
# 任务移交配置
# ============================================

delegate_task() {
    local agent=$1
    local task_type=$2
    local description=$3
    local priority=$4
    
    task_id="$(date +%s%N | cut -b1-13)"
    timestamp=$(date -Iseconds)
    
    cat > $HUB_DIR/inbox/${agent}_${task_id}.json << EOF
{
  "id": "${task_id}",
  "agent": "${agent}",
  "type": "${task_type}",
  "description": "${description}",
  "priority": "${priority}",
  "status": "pending",
  "created_at": "${timestamp}",
  "source": "neural_hub",
  "payload": {}
}
EOF
    
    echo "✅ 已移交: ${agent} → ${task_type}"
}

# ============================================
# 阶段1: 立即移交 (低安全等级)
# ============================================

echo ""
echo "📋 阶段1: 立即移交任务"
echo "----------------------"

# nanobot-1 研究员 - 情报收集
delegate_task "nanobot-1" "monitor" "Polymarket监控 + 情报收集" "normal"

# nanobot-5 分析师 - 数据分析  
delegate_task "nanobot-5" "analysis" "Moltbook活动追踪 + 数据分析" "normal"

# nanobot-8 运维专家 - 系统监控
delegate_task "nanobot-8" "ops" "系统资源监控 + 健康检查" "normal"

# nanobot-6 决策分析师 - 决策支持
delegate_task "nanobot-6" "decision" "学习债务评估 + 决策报告" "low"

# ============================================
# 阶段2: 待激活任务 (需要适配)
# ============================================

echo ""
echo "📋 阶段2: 待激活任务 (已暂停)"
echo "------------------------------"

# 这些任务暂不激活，保持精简模式
# delegate_task "nanobot-7" "code_review" "代码精简 + 质量检查" "low"
# delegate_task "nanobot-9" "strategy" "超进化引擎 + 长期规划" "low"
# delegate_task "nanobot-4" "security" "安全审计 + 漏洞扫描" "normal"
# delegate_task "nanobot-3" "coding" "自动化脚本开发" "normal"

# ============================================
# 阶段3: 保留在神经中枢 (安全关键)
# ============================================

echo ""
echo "🔒 阶段3: 保留在神经中枢 (P0安全关键)"
echo "--------------------------------------"
echo "❌ 死手开关系统 - 保留"
echo "❌ 健康快照 - 保留"  
echo "❌ 日志清理 - 保留"

# ============================================
# 状态总结
# ============================================

echo ""
echo "📊 移交状态"
echo "-----------"
echo "精简模式: 3个核心任务保留 + 4个任务已移交"
echo "活跃Agent: 10/10"
echo "待处理任务: $(ls $HUB_DIR/inbox/*.json 2>/dev/null | wc -l)"
echo ""
echo "✅ 移交完成"
