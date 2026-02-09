#!/bin/bash
# safe-exec.sh - 安全的命令执行包装器
# 在执行任何命令前进行安全检查

SELF_PROTECT_SCRIPT="/root/.openclaw/workspace/scripts/self-protection.sh"

# 加载自我保护检查
source "$SELF_PROTECT_SCRIPT" 2>/dev/null || true

# 命令分类检查
classify_command() {
    local cmd="$1"
    
    # 极度危险 - 阻止
    if [[ "$cmd" == *"rm -rf /"* ]] || [[ "$cmd" == *"rm -rf ~"* ]] || \
       [[ "$cmd" == *"mkfs."* ]] || [[ "$cmd" == *":(){ :|:& };:"* ]] || \
       [[ "$cmd" == *"> /dev/sda"* ]] || [[ "$cmd" == *"chmod -R 777 /"* ]]; then
        echo "DANGER"
        return
    fi
    
    # 高风险 - 需要快照
    if [[ "$cmd" == *"rm -rf"* ]] || [[ "$cmd" == *"systemctl stop"* ]] || \
       [[ "$cmd" == *"openclaw gateway config.apply"* ]] || \
       [[ "$cmd" == *"killall"* ]] || [[ "$cmd" == *"pkill -9"* ]]; then
        echo "HIGH_RISK"
        return
    fi
    
    # 中风险 - 需要检查
    if [[ "$cmd" == *"npx clawhub install"* ]] || [[ "$cmd" == *"npm install"* ]] || \
       [[ "$cmd" == *"pip install"* ]] || [[ "$cmd" == *"curl"*"|"*"sh"* ]] || \
       [[ "$cmd" == *"wget"*"|"*"sh"* ]]; then
        echo "MEDIUM_RISK"
        return
    fi
    
    echo "NORMAL"
}

# 主函数
main() {
    local cmd="$*"
    local risk_level=$(classify_command "$cmd")
    
    echo "🔒 安全执行检查"
    echo "   命令: $cmd"
    echo "   风险等级: $risk_level"
    
    case "$risk_level" in
        "DANGER")
            echo "❌ 此命令极度危险，已被阻止！"
            echo "   可能导致系统完全损坏。"
            exit 1
            ;;
        "HIGH_RISK")
            echo "⚠️  此命令高风险，正在创建快照..."
            bash /root/.openclaw/workspace/scripts/backup-simple.sh >/dev/null 2>&1
            echo "   ✅ 快照已创建"
            ;;
        "MEDIUM_RISK")
            echo "⚡ 中风险操作，执行中..."
            ;;
        "NORMAL")
            echo "✅ 正常操作"
            ;;
    esac
    
    # 执行原始命令
    echo "   执行: $cmd"
    echo "---"
    exec bash -c "$cmd"
}

# 如果不是直接运行，则作为库加载
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
