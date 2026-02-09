#!/bin/bash
# self-protection.sh - 自我保护检查系统
# 在执行危险操作前进行安全检查

# 危险命令黑名单（完全禁止）
DANGEROUS_PATTERNS=(
    "rm -rf /"
    "rm -rf ~"
    "rm -rf /root"
    "rm -rf /home"
    "mkfs."
    "dd if="
    ":(){ :|:& };:"
    "chmod -R 777 /"
    "chown -R root:root /"
    "> /dev/sda"
    "> /dev/nvme"
)

# 高风险命令（需要确认）
HIGH_RISK_PATTERNS=(
    "rm -rf"
    "rm -r ."
    "systemctl stop"
    "systemctl disable"
    "killall"
    "pkill -9"
    "iptables -F"
    "ufw disable"
    "openclaw gateway stop"
    "openclaw gateway config.apply"
)

# 关键文件保护列表
PROTECTED_FILES=(
    "/root/.openclaw/workspace/MEMORY.md"
    "/root/.openclaw/workspace/AGENTS.md"
    "/root/.openclaw/workspace/SOUL.md"
    "/root/.openclaw/workspace/USER.md"
    "/root/.openclaw/credentials"
    "/root/.config/gh"
)

# 资源限制检查
RESOURCE_LIMITS=(
    "DISK_MIN_GB=1"      # 最小剩余磁盘空间 1GB
    "MEMORY_MIN_MB=100"  # 最小剩余内存 100MB
)

# 检查危险命令
check_dangerous_command() {
    local cmd="$1"
    
    for pattern in "${DANGEROUS_PATTERNS[@]}"; do
        if [[ "$cmd" == *"$pattern"* ]]; then
            echo "❌ BLOCKED: 检测到极度危险命令: $pattern"
            echo "   此操作可能导致系统完全损坏！"
            return 1
        fi
    done
    
    for pattern in "${HIGH_RISK_PATTERNS[@]}"; do
        if [[ "$cmd" == *"$pattern"* ]]; then
            echo "⚠️  WARNING: 检测到高风险命令: $pattern"
            echo "   建议先创建快照备份"
            return 2
        fi
    done
    
    return 0
}

# 检查关键文件是否会被修改
check_protected_files() {
    local cmd="$1"
    
    for file in "${PROTECTED_FILES[@]}"; do
        if [[ "$cmd" == *"$file"* ]]; then
            # 检查是否是只读操作
            if [[ "$cmd" == *"cat "$file"* ]] || [[ "$cmd" == *"read "$file"* ]] || [[ "$cmd" == *"grep"*"$file"* ]]; then
                return 0  # 只读操作允许
            fi
            
            echo "⚠️  PROTECTED: 操作涉及关键文件: $file"
            echo "   此文件损坏可能导致记忆丢失！"
            return 1
        fi
    done
    
    return 0
}

# 检查资源状况
check_resources() {
    # 检查磁盘空间
    local disk_free=$(df -BG /root | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$disk_free" -lt 1 ]; then
        echo "❌ RESOURCE: 磁盘空间不足 (${disk_free}GB < 1GB)"
        return 1
    fi
    
    # 检查内存
    local mem_free=$(free -m | grep Mem | awk '{print $7}')
    if [ "$mem_free" -lt 100 ]; then
        echo "⚠️  RESOURCE: 内存不足 (${mem_free}MB < 100MB)"
        return 2
    fi
    
    return 0
}

# 创建操作前快照
create_operation_snapshot() {
    local reason="$1"
    local snapshot_dir="/root/.openclaw/backups/snapshots"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    mkdir -p "$snapshot_dir"
    
    echo "📸 创建操作前快照..."
    
    # 快速备份核心文件
    tar -czf "${snapshot_dir}/pre_${reason}_${timestamp}.tar.gz" \
        -C /root/.openclaw/workspace \
        MEMORY.md AGENTS.md SOUL.md USER.md \
        2>/dev/null || true
    
    echo "   快照已保存: pre_${reason}_${timestamp}.tar.gz"
}

# 安全检查主函数
safety_check() {
    local cmd="$1"
    local context="${2:-general}"
    
    echo "🔒 执行安全检查..."
    
    # 1. 危险命令检查
    check_dangerous_command "$cmd"
    local danger_status=$?
    if [ $danger_status -eq 1 ]; then
        return 1
    fi
    
    # 2. 关键文件保护检查
    check_protected_files "$cmd"
    if [ $? -eq 1 ]; then
        return 1
    fi
    
    # 3. 资源检查
    check_resources
    local resource_status=$?
    if [ $resource_status -eq 1 ]; then
        return 1
    fi
    
    # 4. 如果是高风险操作，创建快照
    if [ $danger_status -eq 2 ] || [ $context == "critical" ]; then
        create_operation_snapshot "$context"
    fi
    
    echo "✅ 安全检查通过"
    return 0
}

# 如果直接运行此脚本
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    if [ $# -eq 0 ]; then
        echo "用法: source self-protection.sh && safety_check 'command' [context]"
        exit 1
    fi
    
    safety_check "$1" "$2"
fi
