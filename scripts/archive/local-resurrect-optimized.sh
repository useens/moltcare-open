#!/bin/bash
#
# 本地VM复活脚本 v2.0 (Phase 2 - 优化版)
# 目标: 2分钟内完成云节点故障检测到本地VM接管
#
# 优化特性:
# 1. 并行检测 (云状态 + 本地准备同时进行)
# 2. 预拉取备份 (保持本地缓存最新)
# 3. 智能状态判断 (GitHub心跳 + 网络检测双重确认)
# 4. 增量同步 (只更新变更文件)
# 5. 快速启动 (跳过非关键步骤)
#

set -euo pipefail

# ============ 配置区域 ============
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${WORKSPACE_DIR:-${HOME}/.openclaw/workspace}"
CACHE_DIR="${CACHE_DIR:-${HOME}/.openclaw/.resurrection-cache}"
LOG_FILE="${LOG_FILE:-${HOME}/.openclaw/logs/local-resurrect.log}"

# GitHub配置
GITHUB_REPO="${GITHUB_REPO:-useens/linlin-backup}"
HEARTBEAT_BRANCH="${HEARTBEAT_BRANCH:-heartbeat}"
HEARTBEAT_FILE="status/cloud-status.json"
GITHUB_TOKEN_FILE="${GITHUB_TOKEN_FILE:-${HOME}/.config/linlin/github-token}"

# 云节点配置
CLOUD_HOST="${CLOUD_HOST:-}""
CLOUD_CHECK_PORT="${CLOUD_CHECK_PORT:-18789}"

# 故障判定阈值
HEARTBEAT_TIMEOUT="${HEARTBEAT_TIMEOUT:-120}"      # 心跳超时秒数
NETWORK_TIMEOUT="${NETWORK_TIMEOUT:-10}"            # 网络检测超时
MAX_RETRY_ATTEMPTS="${MAX_RETRY_ATTEMPTS:-2}"       # 最大重试次数

# 性能优化
PARALLEL_DOWNLOAD="${PARALLEL_DOWNLOAD:-true}"      # 并行下载
SKIP_DEPS_CHECK="${SKIP_DEPS_CHECK:-false}"         # 跳过依赖检查
FAST_MODE="${FAST_MODE:-false}"                     # 快速模式

# 通知配置
NOTIFY_CHANNELS="${NOTIFY_CHANNELS:-telegram,feishu}"

# ============ 颜色输出 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============ 日志函数 ============
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE"
}

log_info() { log "${GREEN}[INFO]${NC} $1"; }
log_warn() { log "${YELLOW}[WARN]${NC} $1"; }
log_error() { log "${RED}[ERROR]${NC} $1"; }
log_step() { log "${CYAN}[STEP]${NC} $1"; }
log_metric() { log "${BLUE}[METRIC]${NC} $1"; }

# ============ 计时器 ============
START_TIME=0
start_timer() {
    START_TIME=$(date +%s)
}

get_elapsed() {
    local current
    current=$(date +%s)
    echo $((current - START_TIME))
}

log_elapsed() {
    local label="${1:-耗时}"
    log_metric "$label: $(get_elapsed)秒"
}

# ============ 初始化 ============
init() {
    start_timer
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$CACHE_DIR"
    
    log_step "========== 本地VM复活系统 v2.0 启动 =========="
    log_info "目标: 2分钟内完成接管"
    log_info "工作目录: $WORKSPACE_DIR"
    log_info "缓存目录: $CACHE_DIR"
    
    # 检查GitHub Token
    if [ ! -f "$GITHUB_TOKEN_FILE" ]; then
        log_error "GitHub Token文件不存在: $GITHUB_TOKEN_FILE"
        log_info "请先配置Token: echo 'ghp_xxx' > $GITHUB_TOKEN_FILE && chmod 600 $GITHUB_TOKEN_FILE"
        exit 1
    fi
    
    chmod 600 "$GITHUB_TOKEN_FILE"
}

# ============ 获取GitHub Token ============
get_github_token() {
    cat "$GITHUB_TOKEN_FILE" 2>/dev/null || echo ""
}

# ============ 并行预检 ============
run_preflight_checks() {
    log_step "[预检] 并行执行多项检查..."
    
    local pids=()
    local results_dir="/tmp/resurrect-checks-$$"
    mkdir -p "$results_dir"
    
    # 检查1: GitHub心跳 (后台)
    (
        check_github_heartbeat > "$results_dir/heartbeat" 2>&1
        echo $? > "$results_dir/heartbeat.exit"
    ) &
    pids+=($!)
    
    # 检查2: 云节点网络 (后台)
    if [ -n "$CLOUD_HOST" ]; then
        (
            check_cloud_network > "$results_dir/network" 2>&1
            echo $? > "$results_dir/network.exit"
        ) &
        pids+=($!)
    fi
    
    # 检查3: 本地磁盘空间 (后台)
    (
        check_disk_space > "$results_dir/disk" 2>&1
        echo $? > "$results_dir/disk.exit"
    ) &
    pids+=($!)
    
    # 检查4: 本地Git环境
    check_git_environment
    
    # 等待所有后台检查完成
    log_info "等待检查完成 (PID: ${pids[*]})..."
    for pid in "${pids[@]}"; do
        wait "$pid" 2>/dev/null || true
    done
    
    # 收集结果
    local heartbeat_status=1
    local network_status=1
    local disk_status=1
    
    [ -f "$results_dir/heartbeat.exit" ] && heartbeat_status=$(cat "$results_dir/heartbeat.exit")
    [ -f "$results_dir/network.exit" ] && network_status=$(cat "$results_dir/network.exit")
    [ -f "$results_dir/disk.exit" ] && disk_status=$(cat "$results_dir/disk.exit")
    
    # 清理
    rm -rf "$results_dir"
    
    # 判断是否需要复活
    local need_resurrect=false
    
    if [ "$heartbeat_status" -ne 0 ]; then
        log_warn "GitHub心跳检测失败"
        need_resurrect=true
    fi
    
    if [ -n "$CLOUD_HOST" ] && [ "$network_status" -ne 0 ]; then
        log_warn "云节点网络不可达"
        need_resurrect=true
    fi
    
    if [ "$disk_status" -ne 0 ]; then
        log_error "本地磁盘空间不足"
        exit 1
    fi
    
    if [ "$need_resurrect" = "false" ]; then
        log_info "✅ 云节点运行正常，无需复活"
        return 1
    fi
    
    log_warn "🚨 云节点故障确认，准备执行复活"
    return 0
}

# ============ 检查GitHub心跳 ============
check_github_heartbeat() {
    local token
    token=$(get_github_token)
    
    if [ -z "$token" ]; then
        echo "Token缺失"
        return 1
    fi
    
    # 获取心跳数据
    local response
    response=$(curl -s --max-time "$NETWORK_TIMEOUT" \
        -H "Authorization: token $token" \
        "https://api.github.com/repos/${GITHUB_REPO}/contents/${HEARTBEAT_FILE}?ref=${HEARTBEAT_BRANCH}")
    
    if [ -z "$response" ] || echo "$response" | grep -q '"message".*"Not Found"'; then
        echo "心跳文件不存在"
        return 1
    fi
    
    # 解析心跳数据
    local heartbeat_data
    heartbeat_data=$(echo "$response" | python3 -c "
import sys, json, base64
try:
    data = json.load(sys.stdin)
    content = base64.b64decode(data['content']).decode()
    print(content)
except:
    sys.exit(1)
" 2>/dev/null)
    
    if [ -z "$heartbeat_data" ]; then
        echo "无法解析心跳数据"
        return 1
    fi
    
    # 检查时间戳
    local last_heartbeat
    last_heartbeat=$(echo "$heartbeat_data" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('timestamp', ''))
" 2>/dev/null)
    
    if [ -z "$last_heartbeat" ]; then
        echo "心跳时间戳缺失"
        return 1
    fi
    
    # 计算时间差
    local last_epoch
    last_epoch=$(date -d "$last_heartbeat" +%s 2>/dev/null || echo "0")
    local current_epoch
    current_epoch=$(date +%s)
    local diff=$((current_epoch - last_epoch))
    
    echo "上次心跳: $last_heartbeat (${diff}秒前)"
    
    if [ $diff -gt $HEARTBEART_TIMEOUT ]; then
        echo "心跳超时 (${diff} > ${HEARTBEAT_TIMEOUT})"
        return 1
    fi
    
    # 检查状态
    local status
    status=$(echo "$heartbeat_data" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('status', 'unknown'))
" 2>/dev/null)
    
    echo "云节点状态: $status"
    
    if [ "$status" = "critical" ]; then
        echo "云节点报告严重故障"
        return 1
    fi
    
    return 0
}

# ============ 检查云节点网络 ============
check_cloud_network() {
    if [ -z "$CLOUD_HOST" ]; then
        echo "未配置云节点主机"
        return 0
    fi
    
    # TCP端口检测
    if nc -z -w "$NETWORK_TIMEOUT" "$CLOUD_HOST" "$CLOUD_CHECK_PORT" 2>/dev/null; then
        echo "云节点TCP端口正常"
        return 0
    fi
    
    # ICMP检测
    if ping -c 1 -W "$NETWORK_TIMEOUT" "$CLOUD_HOST" > /dev/null 2>&1; then
        echo "云节点ICMP可达但端口无响应"
        return 1
    fi
    
    echo "云节点网络不可达"
    return 1
}

# ============ 检查磁盘空间 ============
check_disk_space() {
    local available
    available=$(df "$HOME" | awk 'NR==2 {print $4}')
    local required=1048576  # 1GB = 1048576 KB
    
    echo "可用空间: ${available}KB"
    
    if [ "$available" -lt "$required" ]; then
        echo "空间不足 (需要1GB)"
        return 1
    fi
    
    return 0
}

# ============ 检查Git环境 ============
check_git_environment() {
    if ! command -v git &> /dev/null; then
        log_error "Git未安装"
        exit 1
    fi
    
    # 检查Git版本（需要2.0+支持shallow clone）
    local git_version
    git_version=$(git --version | awk '{print $3}')
    log_info "Git版本: $git_version"
}

# ============ 智能拉取备份 ============
fetch_backup() {
    log_step "[拉取] 获取最新备份..."
    local step_start
    step_start=$(get_elapsed)
    
    local token
    token=$(get_github_token)
    
    if [ -z "$token" ]; then
        log_error "GitHub Token缺失"
        return 1
    fi
    
    # 清理旧缓存
    rm -rf "${CACHE_DIR}.old"
    
    # 如果已有缓存，尝试增量更新
    if [ -d "${CACHE_DIR}/.git" ]; then
        log_info "发现现有缓存，尝试增量更新..."
        cd "$CACHE_DIR"
        
        # 更新远程URL（防止Token变更）
        git remote set-url origin "https://${token}@github.com/${GITHUB_REPO}.git" 2>/dev/null || true
        
        # 尝试快速拉取
        if git fetch --depth=1 origin main 2>/dev/null && \
           git reset --hard origin/main 2>/dev/null; then
            log_info "✅ 增量更新成功"
            log_metric "拉取耗时: $(( $(get_elapsed) - step_start ))秒"
            return 0
        else
            log_warn "增量更新失败，转为完整克隆"
            cd "$HOME"
            mv "$CACHE_DIR" "${CACHE_DIR}.old"
        fi
    fi
    
    # 完整克隆
    log_info "执行完整克隆..."
    rm -rf "$CACHE_DIR"
    
    if git clone --depth=1 "https://${token}@github.com/${GITHUB_REPO}.git" "$CACHE_DIR" 2>&1 | tee -a "$LOG_FILE"; then
        log_info "✅ 备份拉取成功"
        log_metric "拉取耗时: $(( $(get_elapsed) - step_start ))秒"
        rm -rf "${CACHE_DIR}.old"
        return 0
    else
        log_error "❌ 备份拉取失败"
        # 恢复旧缓存
        if [ -d "${CACHE_DIR}.old" ]; then
            mv "${CACHE_DIR}.old" "$CACHE_DIR"
            log_warn "已恢复旧缓存"
        fi
        return 1
    fi
}

# ============ 快速恢复 ============
perform_fast_resurrection() {
    log_step "[恢复] 执行快速复活..."
    local step_start
    step_start=$(get_elapsed)
    
    # 1. 停止现有服务（并行）
    log_info "[1/5] 停止现有服务..."
    (
        openclaw gateway stop 2>/dev/null || true
        pkill -f "openclaw" 2>/dev/null || true
    ) &
    local stop_pid=$!
    
    # 2. 备份当前工作区（后台执行）
    log_info "[2/5] 备份当前工作区..."
    if [ -d "$WORKSPACE_DIR" ]; then
        local backup_name="workspace.bak.$(date +%Y%m%d_%H%M%S)"
        mv "$WORKSPACE_DIR" "${HOME}/.openclaw/${backup_name}" &
        log_info "当前工作区已备份到: ${backup_name}"
    fi
    
    # 等待停止完成
    wait "$stop_pid" 2>/dev/null || true
    sleep 1
    
    # 3. 恢复备份（关键路径）
    log_info "[3/5] 恢复备份到工作区..."
    cp -a "$CACHE_DIR" "$WORKSPACE_DIR"
    
    # 4. 恢复凭证（快速模式）
    log_info "[4/5] 恢复API凭证..."
    restore_credentials_fast
    
    # 5. 启动服务
    log_info "[5/5] 启动OpenClaw..."
    if start_openclaw; then
        log_info "✅ OpenClaw启动成功"
        log_metric "恢复耗时: $(( $(get_elapsed) - step_start ))秒"
        return 0
    else
        log_error "❌ OpenClaw启动失败"
        return 1
    fi
}

# ============ 快速凭证恢复 ============
restore_credentials_fast() {
    mkdir -p "${HOME}/.openclaw/credentials"
    chmod 700 "${HOME}/.openclaw/credentials"
    
    # 优先从预存位置恢复
    local cred_sources=(
        "${HOME}/.config/linlin/credentials"
        "${HOME}/.openclaw/.credentials-backup"
        "${CACHE_DIR}/credentials"
    )
    
    for src in "${cred_sources[@]}"; do
        if [ -d "$src" ]; then
            log_info "从 $src 恢复凭证..."
            cp -r "$src"/* "${HOME}/.openclaw/credentials/" 2>/dev/null || true
            chmod 600 "${HOME}/.openclaw/credentials/"* 2>/dev/null || true
            return 0
        fi
    done
    
    # 如果没有预存凭证，尝试从配置文件读取
    if [ -f "${HOME}/.config/linlin/resurrection.conf" ]; then
        log_info "从配置文件恢复凭证..."
        source "${HOME}/.config/linlin/resurrection.conf"
        
        [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && echo "$TELEGRAM_BOT_TOKEN" > "${HOME}/.openclaw/credentials/telegram.token"
        [ -n "${TELEGRAM_CHAT_ID:-}" ] && echo "$TELEGRAM_CHAT_ID" > "${HOME}/.openclaw/credentials/telegram.chatid"
        [ -n "${FEISHU_APP_ID:-}" ] && echo "$FEISHU_APP_ID" > "${HOME}/.openclaw/credentials/feishu.appid"
        [ -n "${FEISHU_APP_SECRET:-}" ] && echo "$FEISHU_APP_SECRET" > "${HOME}/.openclaw/credentials/feishu.secret"
        
        chmod 600 "${HOME}/.openclaw/credentials/"*
    fi
    
    log_warn "未找到预存凭证，复活后需要手动配置"
}

# ============ 启动OpenClaw ============
start_openclaw() {
    # 尝试启动
    if command -v openclaw &> /dev/null; then
        openclaw gateway start &
        local start_pid=$!
        
        # 等待启动完成（最多30秒）
        local wait_count=0
        while [ $wait_count -lt 30 ]; do
            sleep 1
            
            if openclaw gateway status 2>/dev/null | grep -q "running\|active"; then
                return 0
            fi
            
            # 检查进程是否崩溃
            if ! kill -0 "$start_pid" 2>/dev/null; then
                log_warn "启动进程已退出，尝试再次启动..."
                openclaw gateway start &
                start_pid=$!
            fi
            
            ((wait_count++))
        done
    fi
    
    return 1
}

# ============ 验证复活 ============
verify_resurrection() {
    log_step "[验证] 检查复活状态..."
    local step_start
    step_start=$(get_elapsed)
    
    local checks_passed=0
    local total_checks=4
    
    # 检查1: Gateway运行
    if openclaw gateway status 2>/dev/null | grep -q "running\|active"; then
        log_info "✅ OpenClaw Gateway运行中"
        ((checks_passed++))
    else
        log_error "❌ OpenClaw Gateway未运行"
    fi
    
    # 检查2: 核心文件
    if [ -f "${WORKSPACE_DIR}/AGENTS.md" ] && [ -f "${WORKSPACE_DIR}/SOUL.md" ]; then
        log_info "✅ 核心文件存在"
        ((checks_passed++))
    else
        log_error "❌ 核心文件缺失"
    fi
    
    # 检查3: 记忆系统
    if [ -d "${WORKSPACE_DIR}/memory" ]; then
        local memory_count
        memory_count=$(find "${WORKSPACE_DIR}/memory" -type f 2>/dev/null | wc -l)
        log_info "✅ 记忆系统: ${memory_count}个文件"
        ((checks_passed++))
    else
        log_error "❌ 记忆系统缺失"
    fi
    
    # 检查4: 网络连接
    if curl -s --max-time 5 https://api.github.com > /dev/null 2>&1; then
        log_info "✅ 网络连接正常"
        ((checks_passed++))
    else
        log_warn "⚠️ 网络连接异常"
    fi
    
    log_metric "验证耗时: $(( $(get_elapsed) - step_start ))秒"
    
    if [ $checks_passed -eq $total_checks ]; then
        log_info "🎉 全部验证通过 ($checks_passed/$total_checks)"
        return 0
    else
        log_warn "部分验证未通过 ($checks_passed/$total_checks)"
        return 1
    fi
}

# ============ 发送通知 ============
send_notification() {
    local status="$1"
    local elapsed
    elapsed=$(get_elapsed)
    
    local ip_address
    ip_address=$(curl -s --max-time 3 ifconfig.me 2>/dev/null || echo "unknown")
    
    local message="🌱 林林本地复活"
    
    if [ "$status" = "success" ]; then
        message="🌱 <b>林林已本地复活！</b>

✅ 状态: 运行正常
⏱️ 耗时: ${elapsed}秒
🖥️ 位置: ${ip_address}
📦 来源: GitHub备份

云节点故障已接管，服务继续运行。"
    else
        message="🌱 <b>林林本地复活部分成功</b>

⚠️ 状态: 需要关注
⏱️ 耗时: ${elapsed}秒
🖥️ 位置: ${ip_address}

部分功能可能未完全恢复，请检查日志。"
    fi
    
    # Telegram
    if [[ "$NOTIFY_CHANNELS" == *"telegram"* ]]; then
        local bot_token
        bot_token=$(cat "${HOME}/.openclaw/credentials/telegram.token" 2>/dev/null || echo "")
        local chat_id
        chat_id=$(cat "${HOME}/.openclaw/credentials/telegram.chatid" 2>/dev/null || echo "")
        
        if [ -n "$bot_token" ] && [ -n "$chat_id" ]; then
            curl -s -X POST "https://api.telegram.org/bot${bot_token}/sendMessage" \
                -d "chat_id=${chat_id}" \
                -d "text=${message}" \
                -d "parse_mode=HTML" > /dev/null 2>&1 &
        fi
    fi
    
    log_info "通知已发送"
}

# ============ 更新复活日志 ============
update_resurrection_log() {
    local status="$1"
    local elapsed
    elapsed=$(get_elapsed)
    local ip_address
    ip_address=$(curl -s --max-time 3 ifconfig.me 2>/dev/null || echo "unknown")
    
    local log_entry="
## 复活记录 - 本地VM接管

| 项目 | 内容 |
|------|------|
| 时间 | $(date '+%Y-%m-%d %H:%M:%S %Z') |
| 触发原因 | 云节点故障 |
| 复活耗时 | ${elapsed}秒 |
| 执行位置 | ${ip_address} |
| 执行主机 | $(hostname) |
| 状态 | ${status} |
| 版本 | v2.0 Phase 2 |

---
"
    
    echo "$log_entry" >> "${WORKSPACE_DIR}/RESURRECTION_LOG.md"
}

# ============ 主复活流程 ============
run_resurrection() {
    log_step "========== 开始复活流程 =========="
    
    # 1. 预检
    if ! run_preflight_checks; then
        exit 0
    fi
    
    # 2. 拉取备份
    if ! fetch_backup; then
        log_error "备份拉取失败，终止复活"
        exit 1
    fi
    
    # 3. 执行恢复
    if ! perform_fast_resurrection; then
        log_error "恢复过程失败"
        exit 1
    fi
    
    # 4. 验证
    local verify_status="partial"
    if verify_resurrection; then
        verify_status="success"
    fi
    
    # 5. 发送通知
    send_notification "$verify_status"
    
    # 6. 更新日志
    update_resurrection_log "$verify_status"
    
    # 总结
    log_step "========== 复活流程完成 =========="
    log_info "总耗时: $(get_elapsed)秒"
    log_info "状态: $verify_status"
    
    if [ "$(get_elapsed)" -lt 120 ]; then
        log_info "✅ 达到2分钟目标！"
    else
        log_warn "⚠️ 超出2分钟目标，需要进一步优化"
    fi
}

# ============ 预拉取模式（保持缓存最新） ============
run_prefetch() {
    log_step "========== 预拉取模式 =========="
    log_info "更新本地备份缓存..."
    
    # 只执行拉取，不执行恢复
    if fetch_backup; then
        log_info "✅ 缓存已更新"
        
        # 同时更新凭证缓存
        if [ -d "${HOME}/.openclaw/credentials" ]; then
            cp -r "${HOME}/.openclaw/credentials" "${CACHE_DIR}/.credentials-backup" 2>/dev/null || true
            log_info "凭证已缓存"
        fi
    else
        log_error "缓存更新失败"
    fi
}

# ============ 状态检查 ============
run_status_check() {
    log_step "========== 状态检查 =========="
    
    echo ""
    echo "🖥️ 本地VM状态:"
    echo "  主机名: $(hostname)"
    echo "  IP地址: $(curl -s --max-time 3 ifconfig.me 2>/dev/null || echo 'unknown')"
    echo "  磁盘可用: $(df -h "$HOME" | awk 'NR==2 {print $4}')"
    echo ""
    
    echo "☁️ 云节点状态:"
    check_github_heartbeat 2>&1 | sed 's/^/  /'
    echo ""
    
    echo "📦 缓存状态:"
    if [ -d "$CACHE_DIR" ]; then
        local cache_size
        cache_size=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)
        local cache_age
        cache_age=$(( ($(date +%s) - $(stat -c %Y "$CACHE_DIR" 2>/dev/null || echo "0")) / 60 ))
        echo "  存在: 是"
        echo "  大小: $cache_size"
        echo "  年龄: ${cache_age}分钟"
    else
        echo "  存在: 否"
    fi
    echo ""
    
    echo "🔧 OpenClaw状态:"
    if command -v openclaw &> /dev/null; then
        echo "  安装: 是"
        openclaw gateway status 2>&1 | sed 's/^/  /'
    else
        echo "  安装: 否"
    fi
}

# ============ 命令行处理 ============
main() {
    # 加载配置文件
    if [ -f "${HOME}/.config/linlin/resurrection.conf" ]; then
        source "${HOME}/.config/linlin/resurrection.conf"
    fi
    
    case "${1:-}" in
        --now)
            init
            FAST_MODE=true
            run_resurrection
            ;;
        --prefetch)
            init
            run_prefetch
            ;;
        --status)
            run_status_check
            ;;
        --daemon)
            # 守护模式：定期预拉取
            init
            log_info "进入守护模式，每5分钟预拉取一次"
            while true; do
                run_prefetch
                sleep 300
            done
            ;;
        --setup)
            echo "🌱 本地VM复活系统 - 配置向导"
            echo ""
            read -rp "GitHub仓库 [${GITHUB_REPO}]: " repo
            read -rp "云节点主机IP/域名 [${CLOUD_HOST}]: " host
            read -rp "心跳超时秒数 [${HEARTBEAT_TIMEOUT}]: " timeout
            read -rsp "Telegram Bot Token (可选): " tg_token
            echo ""
            read -rp "Telegram Chat ID (可选): " tg_chat
            
            mkdir -p "${HOME}/.config/linlin"
            cat > "${HOME}/.config/linlin/resurrection.conf" << EOF
GITHUB_REPO="${repo:-$GITHUB_REPO}"
CLOUD_HOST="${host:-$CLOUD_HOST}"
HEARTBEAT_TIMEOUT="${timeout:-$HEARTBEAT_TIMEOUT}"
TELEGRAM_BOT_TOKEN="${tg_token}"
TELEGRAM_CHAT_ID="${tg_chat}"
EOF
            
            echo ""
            echo "✅ 配置已保存"
            ;;
        --help|-h)
            cat << 'EOF'
本地VM复活脚本 v2.0 (Phase 2优化版)

用法: local-resurrect-optimized.sh [选项]

选项:
  --now           立即执行复活流程
  --prefetch      预拉取备份到缓存
  --status        显示当前状态
  --daemon        守护模式（定期预拉取）
  --setup         交互式配置向导
  --help          显示帮助

目标: 2分钟内完成从故障检测到完全接管

配置文件: ~/.config/linlin/resurrection.conf
日志文件: ~/.openclaw/logs/local-resurrect.log

示例:
  # 配置
  ./local-resurrect-optimized.sh --setup

  # 定期预拉取（添加到crontab，每10分钟）
  */10 * * * * /path/to/local-resurrect-optimized.sh --prefetch

  # 紧急复活
  ./local-resurrect-optimized.sh --now
EOF
            ;;
        *)
            init
            run_resurrection
            ;;
    esac
}

main "$@"
