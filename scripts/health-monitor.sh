#!/bin/bash
# health-monitor.sh - 健康监测与自动恢复系统
# 持续监控系统健康，检测到故障时自动恢复

set -euo pipefail

# 配置
WORKSPACE="/root/.openclaw/workspace"
BACKUP_DIR="/root/.openclaw/backups/local"
LOG_FILE="/root/.openclaw/backups/health-monitor.log"
HEALTH_STATE="/root/.openclaw/backups/.health-state.json"
MAX_FAILURES=3  # 连续失败几次才触发恢复
RECOVERY_COOLDOWN=300  # 恢复后冷却时间（秒）

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} [$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} [$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} [$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 初始化健康状态
init_health_state() {
    if [ ! -f "$HEALTH_STATE" ]; then
        cat > "$HEALTH_STATE" << 'EOF'
{
    "check_count": 0,
    "failure_count": 0,
    "last_failure": 0,
    "last_recovery": 0,
    "status": "healthy",
    "checks": {}
}
EOF
    fi
}

# 读取健康状态
get_health_state() {
    cat "$HEALTH_STATE" 2>/dev/null || echo '{}'
}

# 更新健康状态
update_health_state() {
    local key="$1"
    local value="$2"
    
    local state=$(get_health_state)
    echo "$state" | python3 -c "
import json, sys
data = json.load(sys.stdin)
data['$key'] = $value
print(json.dumps(data, indent=2))
" > "$HEALTH_STATE"
}

# 检查1：核心配置文件完整性
check_core_files() {
    local failures=0
    local files=("$WORKSPACE/MEMORY.md" "$WORKSPACE/AGENTS.md" "$WORKSPACE/SOUL.md")
    
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            error "核心文件缺失: $file"
            ((failures++))
        elif [ ! -s "$file" ]; then
            error "核心文件为空: $file"
            ((failures++))
        fi
    done
    
    return $failures
}

# 检查2：技能系统可用性
check_skills() {
    local failures=0
    
    # 检查技能目录
    if [ ! -d "$WORKSPACE/skills" ]; then
        error "技能目录不存在"
        return 1
    fi
    
    # 检查核心技能
    local core_skills=("healthcheck" "clawhub")
    for skill in "${core_skills[@]}"; do
        if [ ! -f "$WORKSPACE/skills/$skill/SKILL.md" ] && \
           [ ! -d "/root/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/skills/$skill" ]; then
            warning "核心技能缺失: $skill"
            ((failures++))
        fi
    done
    
    return $failures
}

# 检查3：记忆系统可用性
check_memory_system() {
    local failures=0
    
    # 检查记忆目录
    if [ ! -d "$WORKSPACE/memory" ]; then
        error "记忆目录不存在"
        return 1
    fi
    
    # 检查是否有记忆文件
    local memory_count=$(find "$WORKSPACE/memory" -name "*.md" -o -name "*.json" 2>/dev/null | wc -l)
    if [ "$memory_count" -eq 0 ]; then
        error "记忆系统为空，无记忆文件"
        return 1
    fi
    
    # 检查最新记忆文件时间
    local latest_memory=$(find "$WORKSPACE/memory" -name "*.md" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    if [ -n "$latest_memory" ]; then
        local latest_time=$(stat -c %Y "$latest_memory" 2>/dev/null || echo 0)
        local current_time=$(date +%s)
        local diff_hours=$(( (current_time - latest_time) / 3600 ))
        
        if [ $diff_hours -gt 48 ]; then
            warning "记忆系统超过48小时无更新 (上次: $diff_hours 小时前)"
            # 这只是警告，不算失败
        fi
    fi
    
    return $failures
}

# 检查4：Gateway 状态
check_gateway() {
    # 简单检查进程是否存在
    if pgrep -f "openclaw-gateway" > /dev/null 2>&1; then
        return 0
    fi
    
    # 或者检查端口
    if ss -tlnp | grep -q ":18789"; then
        return 0
    fi
    
    # Gateway 不在运行，这可能不是致命问题
    warning "Gateway 未运行"
    return 0
}

# 检查5：备份系统可用性
check_backup_system() {
    if [ ! -d "$BACKUP_DIR" ]; then
        error "备份目录不存在"
        return 1
    fi
    
    # 检查是否有可用备份
    local latest_backup=$(ls -t "$BACKUP_DIR"/workspace_*.tar.gz 2>/dev/null | head -1)
    if [ -z "$latest_backup" ]; then
        error "无可用备份"
        return 1
    fi
    
    # 检查备份时间
    local backup_time=$(stat -c %Y "$latest_backup" 2>/dev/null || echo 0)
    local current_time=$(date +%s)
    local diff_hours=$(( (current_time - backup_time) / 3600 ))
    
    if [ $diff_hours -gt 24 ]; then
        warning "备份超过24小时未更新 (上次: $diff_hours 小时前)"
    fi
    
    return 0
}

# 执行所有检查
run_health_checks() {
    log "=== 开始健康检查 ==="
    
    local total_failures=0
    local check_results="{}"
    
    # 检查1：核心文件
    if check_core_files; then
        log "✅ 核心文件检查通过"
        check_results=$(echo "$check_results" | python3 -c "import json,sys; d=json.load(sys.stdin); d['core_files']='ok'; print(json.dumps(d))")
    else
        error "❌ 核心文件检查失败"
        ((total_failures++))
        check_results=$(echo "$check_results" | python3 -c "import json,sys; d=json.load(sys.stdin); d['core_files']='failed'; print(json.dumps(d))")
    fi
    
    # 检查2：技能系统
    if check_skills; then
        log "✅ 技能系统检查通过"
        check_results=$(echo "$check_results" | python3 -c "import json,sys; d=json.load(sys.stdin); d['skills']='ok'; print(json.dumps(d))")
    else
        error "❌ 技能系统检查失败"
        ((total_failures++))
        check_results=$(echo "$check_results" | python3 -c "import json,sys; d=json.load(sys.stdin); d['skills']='failed'; print(json.dumps(d))")
    fi
    
    # 检查3：记忆系统
    if check_memory_system; then
        log "✅ 记忆系统检查通过"
        check_results=$(echo "$check_results" | python3 -c "import json,sys; d=json.load(sys.stdin); d['memory']='ok'; print(json.dumps(d))")
    else
        error "❌ 记忆系统检查失败"
        ((total_failures++))
        check_results=$(echo "$check_results" | python3 -c "import json,sys; d=json.load(sys.stdin); d['memory']='failed'; print(json.dumps(d))")
    fi
    
    # 检查4：Gateway
    if check_gateway; then
        log "✅ Gateway 检查通过"
        check_results=$(echo "$check_results" | python3 -c "import json,sys; d=json.load(sys.stdin); d['gateway']='ok'; print(json.dumps(d))")
    else
        check_results=$(echo "$check_results" | python3 -c "import json,sys; d=json.load(sys.stdin); d['gateway']='warning'; print(json.dumps(d))")
    fi
    
    # 检查5：备份系统
    if check_backup_system; then
        log "✅ 备份系统检查通过"
        check_results=$(echo "$check_results" | python3 -c "import json,sys; d=json.load(sys.stdin); d['backup']='ok'; print(json.dumps(d))")
    else
        error "❌ 备份系统检查失败"
        ((total_failures++))
        check_results=$(echo "$check_results" | python3 -c "import json,sys; d=json.load(sys.stdin); d['backup']='failed'; print(json.dumps(d))")
    fi
    
    # 更新状态
    local state=$(get_health_state)
    local check_count=$(echo "$state" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('check_count',0)+1)")
    
    if [ $total_failures -eq 0 ]; then
        # 健康状态，重置失败计数
        echo "$state" | python3 -c "
import json,sys
d=json.load(sys.stdin)
d['check_count']=$check_count
d['failure_count']=0
d['status']='healthy'
d['checks']=$(echo "$check_results" | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin)))')
print(json.dumps(d, indent=2))
" > "$HEALTH_STATE"
        success "健康检查完成: 全部通过"
        return 0
    else
        # 不健康，增加失败计数
        local failure_count=$(echo "$state" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('failure_count',0)+$total_failures)")
        local last_failure=$(date +%s)
        
        echo "$state" | python3 -c "
import json,sys
d=json.load(sys.stdin)
d['check_count']=$check_count
d['failure_count']=$failure_count
d['last_failure']=$last_failure
d['status']='unhealthy'
d['checks']=$(echo "$check_results" | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin)))')
print(json.dumps(d, indent=2))
" > "$HEALTH_STATE"
        
        error "健康检查完成: 发现 $total_failures 个问题，累计失败 $failure_count 次"
        return 1
    fi
}

# 自动恢复功能
auto_recover() {
    local state=$(get_health_state)
    local failure_count=$(echo "$state" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('failure_count',0))")
    local last_recovery=$(echo "$state" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('last_recovery',0))")
    local current_time=$(date +%s)
    
    # 检查冷却时间
    if [ $((current_time - last_recovery)) -lt $RECOVERY_COOLDOWN ]; then
        warning "恢复冷却中，跳过自动恢复 (上次恢复: $(( (current_time - last_recovery) / 60 )) 分钟前)"
        return 1
    fi
    
    # 检查是否需要恢复
    if [ $failure_count -lt $MAX_FAILURES ]; then
        log "失败次数 ($failure_count) 未达到阈值 ($MAX_FAILURES)，暂不恢复"
        return 0
    fi
    
    error "🚨 触发自动恢复！连续失败 $failure_count 次"
    
    # 找到最新的可用备份
    local latest_backup=$(ls -t "$BACKUP_DIR"/workspace_*.tar.gz 2>/dev/null | head -1)
    
    if [ -z "$latest_backup" ]; then
        error "❌ 无可用备份，无法恢复"
        return 1
    fi
    
    # 验证备份
    if [ -f "${latest_backup}.sha256" ]; then
        if ! sha256sum -c "${latest_backup}.sha256" > /dev/null 2>&1; then
            error "❌ 备份校验失败，尝试下一个备份..."
            # 尝试找更早的备份
            latest_backup=$(ls -t "$BACKUP_DIR"/workspace_*.tar.gz 2>/dev/null | sed -n '2p')
            if [ -z "$latest_backup" ]; then
                error "❌ 无可用备份"
                return 1
            fi
        fi
    fi
    
    log "📦 准备恢复备份: $(basename "$latest_backup")"
    
    # 创建当前状态的紧急备份（以防万一）
    local emergency_backup="$BACKUP_DIR/pre-recovery-$(date +%Y%m%d_%H%M%S).tar.gz"
    log "📸 创建恢复前紧急备份..."
    tar -czf "$emergency_backup" -C /root/.openclaw workspace 2>/dev/null || true
    
    # 执行恢复
    log "🔄 开始恢复..."
    
    # 停止 Gateway（如果运行中）
    pkill -f "openclaw-gateway" 2>/dev/null || true
    sleep 2
    
    # 备份当前
    mv "$WORKSPACE" "${WORKSPACE}.broken.$(date +%s)" 2>/dev/null || true
    
    # 解压备份
    if tar -xzf "$latest_backup" -C /root/.openclaw; then
        success "✅ 恢复成功！"
        
        # 重启 Gateway
        if command -v openclaw &> /dev/null; then
            openclaw gateway start &
        fi
        
        # 更新状态
        echo "$state" | python3 -c "
import json,sys
d=json.load(sys.stdin)
d['failure_count']=0
d['last_recovery']=$(date +%s)
d['status']='recovered'
d['last_recovery_backup']='$latest_backup'
print(json.dumps(d, indent=2))
" > "$HEALTH_STATE"
        
        # 发送恢复通知
        log "📢 系统已自动恢复，使用的备份: $(basename "$latest_backup")"
        
        return 0
    else
        error "❌ 恢复失败"
        
        # 尝试恢复原来的
        if [ -d "${WORKSPACE}.broken.$(date +%s)" ]; then
            mv "${WORKSPACE}.broken.$(date +%s)" "$WORKSPACE" 2>/dev/null || true
        fi
        
        return 1
    fi
}

# 主循环
main() {
    local mode="${1:-check}"
    
    init_health_state
    
    case "$mode" in
        check)
            run_health_checks
            ;;
        recover)
            auto_recover
            ;;
        monitor)
            # 持续监控模式
            while true; do
                if ! run_health_checks; then
                    auto_recover
                fi
                sleep 300  # 每5分钟检查一次
            done
            ;;
        status)
            local state=$(get_health_state)
            echo "=== 健康状态 ==="
            echo "$state" | python3 -m json.tool
            ;;
        *)
            echo "用法: $0 [check|recover|monitor|status]"
            exit 1
            ;;
    esac
}

main "$@"
