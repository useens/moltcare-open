#!/bin/bash
# Foundation v2.0 安装脚本

echo "🔧 配置 MoltCare v2.0 运行时..."

# 确保目录存在
mkdir -p ~/.moltcare/runtime
mkdir -p ~/.moltcare/hooks
mkdir -p ~/.moltcare/backups

# 创建运行时集成配置
cat > ~/.moltcare/runtime/openclaw-integration.yaml << 'RUNTIME_EOF'
version: "2.0.0"
integration:
  type: deep
  status: active
  last_sync: ""
  
features:
  multi_agent:
    enabled: true
    auto_trigger: true
    min_signal: 6
    
  memory_system:
    enabled: true
    auto_capture: true
    signal_threshold: 7
    system: vestige
    
  hooks:
    enabled: true
    pre_message: ~/.moltcare/hooks/pre_message.py
    post_message: ~/.moltcare/hooks/post_message.py
    heartbeat: ~/.moltcare/hooks/heartbeat.py
    
  task_queue:
    enabled: true
    system: clawdo
    auto_process: true

sync:
  interval: 300  # 5分钟
  auto_apply_packs: true
  backup_before_merge: true
RUNTIME_EOF

echo "✓ 运行时配置已创建"

# 安装/更新 hooks
if [ ! -f ~/.moltcare/hooks/pre_message.py ]; then
    echo "⚠️  需要运行: moltcare init --force 来安装 hooks"
fi

echo "🎉 Foundation v2.0 配置完成!"
echo ""
echo "新增功能:"
echo "  • 自动触发词检测"
echo "  • 运行时 hooks 集成"  
echo "  • 智能记忆捕获"
echo "  • 定时任务队列"
echo ""
echo "运行 'moltcare doctor' 检查状态"
