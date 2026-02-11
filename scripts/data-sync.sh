#!/bin/bash
# =============================================================================
# 双节点数据双向同步系统 - 主节点同步脚本
# 路径: ~/.openclaw/workspace/scripts/data-sync.sh
# 功能: 实现云端主节点与本地VM的双向数据同步
# =============================================================================

set -euo pipefail

# =============================================================================
# 配置区域
# =============================================================================

# 节点配置
MASTER_NODE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"  # 主节点工作目录
VM_HOST="localhost"                    # VM通过反向隧道连接
VM_PORT="4444"                         # SSH反向隧道端口
VM_USER="linlin"                       # VM用户名
VM_SYNC_DIR="/opt/linlin/workspace"    # VM端同步目录
VM_RECEIVER="/opt/linlin/sync-receiver.sh"  # VM端接收器脚本路径

# 同步目录配置（相对工作目录）
SYNC_DIRS=(
    "memory"
    "scripts"
    # "credentials"  # 可选，默认不同步敏感数据
)

# 同步状态目录
SYNC_STATE_DIR="$MASTER_NODE/.sync-state"
CONFLICT_DIR="$SYNC_STATE_DIR/conflicts"
LOG_DIR="$MASTER_NODE/logs"
LOG_FILE="$LOG_DIR/data-sync.log"
PID_FILE="$SYNC_STATE_DIR/sync.pid"

# 同步配置
SYNC_INTERVAL=1800          # 定时同步间隔（秒）= 30分钟
WATCH_MODE=false            # 是否启用文件监控模式
BATCH_SIZE=100              # 批量传输文件数
RSYNC_OPTS="-avz --partial --progress --stats"
SSH_OPTS="-o ConnectTimeout=10 -o StrictHostKeyChecking=no -p $VM_PORT"

# 冲突解决策略: timestamp|manual|newer|larger
CONFLICT_STRATEGY="timestamp"

# =============================================================================
# 日志函数
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_debug() { [[ "${DEBUG:-}" == "1" ]] && log "DEBUG" "$@"; }

# =============================================================================
# 初始化函数
# =============================================================================

init() {
    # 创建必要的目录
    mkdir -p "$SYNC_STATE_DIR" "$CONFLICT_DIR" "$LOG_DIR"
    
    # 检查VM连接
    if ! check_vm_connection; then
        log_error "无法连接到VM节点，请检查SSH隧道"
        return 1
    fi
    
    log_info "同步系统初始化完成"
    log_info "主节点: $MASTER_NODE"
    log_info "VM节点: $VM_USER@$VM_HOST:$VM_PORT"
    log_info "同步目录: ${SYNC_DIRS[*]}"
}

check_vm_connection() {
    ssh $SSH_OPTS "$VM_USER@$VM_HOST" "echo 'VM_CONNECTED'" &>/dev/null
}

# =============================================================================
# 状态管理
# =============================================================================

save_sync_state() {
    local dir="$1"
    local state_file="$SYNC_STATE_DIR/$(basename "$dir").state"
    
    # 生成文件清单和校验和
    find "$MASTER_NODE/$dir" -type f -exec stat --format='%Y %n' {} \; 2>/dev/null | sort > "$state_file" || true
    log_debug "保存状态: $dir -> $state_file"
}

load_sync_state() {
    local dir="$1"
    local state_file="$SYNC_STATE_DIR/$(basename "$dir").state"
    [[ -f "$state_file" ]] && cat "$state_file" || echo ""
}

# =============================================================================
# 变更检测
# =============================================================================

detect_changes() {
    local dir="$1"
    local old_state="$SYNC_STATE_DIR/$(basename "$dir").state"
    local new_state="$SYNC_STATE_DIR/$(basename "$dir").state.new"
    
    # 生成新状态
    find "$MASTER_NODE/$dir" -type f -exec stat --format='%Y %n' {} \; 2>/dev/null | sort > "$new_state" || true
    
    if [[ ! -f "$old_state" ]]; then
        # 首次同步，所有文件都是新的
        cat "$new_state"
    else
        # 对比差异
        diff "$old_state" "$new_state" 2>/dev/null | grep '^>' | sed 's/^> //' || true
    fi
}

# =============================================================================
# 冲突检测与解决
# =============================================================================

detect_conflicts() {
    local dir="$1"
    local conflicts=()
    
    # 获取两端文件列表和修改时间
    local master_files="$SYNC_STATE_DIR/$(basename "$dir").master.files"
    local vm_files="$SYNC_STATE_DIR/$(basename "$dir").vm.files"
    
    # 获取VM端文件状态
    ssh $SSH_OPTS "$VM_USER@$VM_HOST" "cd $VM_SYNC_DIR && find $dir -type f -exec stat --format='%Y %n' {} \; 2>/dev/null | sort" > "$vm_files" 2>/dev/null || true
    
    # 获取主节点文件状态
    find "$MASTER_NODE/$dir" -type f -exec stat --format='%Y %n' {} \; 2>/dev/null | sort > "$master_files" || true
    
    # 检测冲突（两端都修改）
    while IFS= read -r line; do
        local mtime="${line%% *}"
        local file="${line#* }"
        local rel_path="${file#$MASTER_NODE/}"
        
        # 检查VM端是否存在且修改时间不同
        local vm_line=$(grep " $rel_path$" "$vm_files" 2>/dev/null || true)
        if [[ -n "$vm_line" ]]; then
            local vm_mtime="${vm_line%% *}"
            # 如果时间差超过5秒，认为是冲突
            local time_diff=$((mtime - vm_mtime))
            if [[ ${time_diff#-} -gt 5 ]]; then
                conflicts+=("$rel_path:$mtime:$vm_mtime")
            fi
        fi
    done < "$master_files"
    
    echo "${conflicts[@]}"
}

resolve_conflict() {
    local file="$1"
    local master_mtime="$2"
    local vm_mtime="$3"
    local dir="$4"
    
    local filename=$(basename "$file")
    local conflict_id=$(date +%s)_$(echo "$file" | tr '/' '_')
    
    log_warn "检测到冲突: $file"
    log_warn "  主节点修改时间: $(date -d @$master_mtime '+%Y-%m-%d %H:%M:%S')"
    log_warn "  VM节点修改时间: $(date -d @$vm_mtime '+%Y-%m-%d %H:%M:%S')"
    
    case "$CONFLICT_STRATEGY" in
        "timestamp")
            # 时间戳优先：保留较新的版本
            if [[ $master_mtime -gt $vm_mtime ]]; then
                log_info "策略: 保留主节点版本 (较新)"
                return 0  # 继续同步主节点版本
            else
                log_info "策略: 保留VM节点版本 (较新)"
                return 1  # 跳过此文件
            fi
            ;;
        "manual")
            # 手动合并：保存冲突文件等待处理
            local conflict_path="$CONFLICT_DIR/$conflict_id"
            mkdir -p "$conflict_path"
            
            # 备份本地版本
            cp "$MASTER_NODE/$file" "$conflict_path/master_$filename"
            
            # 获取VM版本
            scp -P $VM_PORT "$VM_USER@$VM_HOST:$VM_SYNC_DIR/$file" "$conflict_path/vm_$filename" 2>/dev/null || true
            
            # 创建冲突标记文件
            cat > "$conflict_path/CONFLICT_INFO.txt" << EOF
冲突文件: $file
主节点修改时间: $(date -d @$master_mtime)
VM节点修改时间: $(date -d @$vm_mtime)
请手动合并后删除此标记文件
EOF
            
            log_warn "冲突文件已保存到: $conflict_path"
            
            # 发送通知
            notify_conflict "$file" "$conflict_path"
            return 1
            ;;
        "newer")
            # 同timestamp
            if [[ $master_mtime -gt $vm_mtime ]]; then
                return 0
            else
                return 1
            fi
            ;;
        *)
            log_error "未知的冲突策略: $CONFLICT_STRATEGY"
            return 1
            ;;
    esac
}

notify_conflict() {
    local file="$1"
    local conflict_path="$2"
    
    # 如果存在通知脚本，调用它
    if [[ -x "$MASTER_NODE/scripts/vm-notify-handler.sh" ]]; then
        "$MASTER_NODE/scripts/vm-notify-handler.sh" "sync_conflict" "$file" "$conflict_path"
    fi
    
    # 同时写入冲突日志
    echo "$(date '+%Y-%m-%d %H:%M:%S') CONFLICT: $file -> $conflict_path" >> "$LOG_DIR/sync-conflicts.log"
}

# =============================================================================
# 同步操作
# =============================================================================

sync_to_vm() {
    local dir="$1"
    local src="$MASTER_NODE/$dir/"
    local dst="$VM_USER@$VM_HOST:$VM_SYNC_DIR/$dir/"
    
    log_info "同步到VM: $dir"
    
    # 检测冲突
    local conflicts=$(detect_conflicts "$dir")
    
    # 构建排除列表
    local exclude_opts=""
    for conflict in $conflicts; do
        local file="${conflict%%:*}"
        local times="${conflict#*:}"
        local master_mtime="${times%%:*}"
        local vm_mtime="${times#*:}"
        
        if ! resolve_conflict "$file" "$master_mtime" "$vm_mtime" "$dir"; then
            exclude_opts="$exclude_opts --exclude=$file"
            log_info "排除冲突文件: $file"
        fi
    done
    
    # 执行rsync
    if rsync $RSYNC_OPTS $SSH_OPTS $exclude_opts "$src" "$dst" 2>&1 | tee -a "$LOG_FILE"; then
        log_info "同步到VM完成: $dir"
        save_sync_state "$dir"
        return 0
    else
        log_error "同步到VM失败: $dir"
        return 1
    fi
}

sync_from_vm() {
    local dir="$1"
    local src="$VM_USER@$VM_HOST:$VM_SYNC_DIR/$dir/"
    local dst="$MASTER_NODE/$dir/"
    
    log_info "从VM同步: $dir"
    
    # 检测VM端变更
    local vm_changes=$(ssh $SSH_OPTS "$VM_USER@$VM_HOST" "cd $VM_SYNC_DIR && find $dir -type f -newer $dir/.last_sync 2>/dev/null | head -$BATCH_SIZE" || true)
    
    if [[ -z "$vm_changes" ]]; then
        log_info "VM端无新变更: $dir"
        return 0
    fi
    
    # 执行rsync（从VM拉取）
    if rsync $RSYNC_OPTS $SSH_OPTS "$src" "$dst" 2>&1 | tee -a "$LOG_FILE"; then
        log_info "从VM同步完成: $dir"
        # 更新VM端同步标记
        ssh $SSH_OPTS "$VM_USER@$VM_HOST" "cd $VM_SYNC_DIR && touch $dir/.last_sync" || true
        return 0
    else
        log_error "从VM同步失败: $dir"
        return 1
    fi
}

bidirectional_sync() {
    local dir="$1"
    
    log_info "开始双向同步: $dir"
    
    # 第一步：从VM获取更新
    sync_from_vm "$dir"
    
    # 第二步：向VM推送更新
    sync_to_vm "$dir"
    
    log_info "双向同步完成: $dir"
}

# =============================================================================
# 文件监控模式
# =============================================================================

watch_mode() {
    log_info "启动文件监控模式..."
    
    if ! command -v inotifywait &>/dev/null; then
        log_error "inotifywait 未安装，无法启用监控模式"
        log_info "请安装 inotify-tools: apt-get install inotify-tools"
        return 1
    fi
    
    # 监控所有同步目录
    local watch_paths=""
    for dir in "${SYNC_DIRS[@]}"; do
        watch_paths="$watch_paths $MASTER_NODE/$dir"
    done
    
    log_info "监控路径: $watch_paths"
    
    # 使用inotifywait监控文件变更
    inotifywait -m -r -e modify,create,delete,move --format '%w%f %e %T' --timefmt '%s' $watch_paths 2>/dev/null | while read file event timestamp; do
        # 防抖处理：等待1秒，聚合快速连续的变更
        sleep 1
        
        # 确定变更的目录
        for dir in "${SYNC_DIRS[@]}"; do
            if [[ "$file" == "$MASTER_NODE/$dir"* ]]; then
                log_info "检测到变更: $file ($event)"
                
                # 延迟同步，避免频繁触发
                (
                    flock -n 200 || exit 0
                    sleep 5  # 等待5秒，聚合更多变更
                    sync_to_vm "$dir"
                ) 200>"$SYNC_STATE_DIR/$dir.lock"
                break
            fi
        done
    done
}

# =============================================================================
# 定时同步
# =============================================================================

scheduled_sync() {
    log_info "执行定时同步..."
    
    for dir in "${SYNC_DIRS[@]}"; do
        if [[ -d "$MASTER_NODE/$dir" ]]; then
            bidirectional_sync "$dir"
        else
            log_warn "目录不存在，跳过: $dir"
        fi
    done
    
    log_info "定时同步完成"
}

# =============================================================================
# 命令行接口
# =============================================================================

show_help() {
    cat << EOF
双节点数据双向同步系统

用法: $(basename "$0") [命令] [选项]

命令:
    init              初始化同步系统
    sync [dir]        执行单次双向同步（指定目录或全部）
    push [dir]        单向推送（主节点 -> VM）
    pull [dir]        单向拉取（VM -> 主节点）
    watch             启动文件监控模式（事件触发）
    daemon            后台守护进程模式（定时+事件）
    status            查看同步状态
    conflicts         查看未解决的冲突
    resolve <file>    手动解决冲突
    test              测试VM连接
    stop              停止守护进程

选项:
    -c, --conflict <strategy>   冲突策略: timestamp|manual|newer (默认: timestamp)
    -i, --interval <seconds>    定时同步间隔 (默认: 1800)
    -d, --debug                 启用调试模式
    -h, --help                  显示帮助

示例:
    # 初始化并测试连接
    $(basename "$0") init
    $(basename "$0") test

    # 执行完整同步
    $(basename "$0") sync

    # 只同步memory目录
    $(basename "$0") sync memory

    # 启动监控模式
    $(basename "$0") watch

    # 后台守护进程
    $(basename "$0") daemon

    # 查看冲突
    $(basename "$0") conflicts
EOF
}

show_status() {
    echo "========== 同步系统状态 =========="
    echo "主节点路径: $MASTER_NODE"
    echo "VM连接: $VM_USER@$VM_HOST:$VM_PORT"
    
    if check_vm_connection; then
        echo "VM状态: 已连接 ✓"
    else
        echo "VM状态: 未连接 ✗"
    fi
    
    echo ""
    echo "同步目录:"
    for dir in "${SYNC_DIRS[@]}"; do
        local state_file="$SYNC_STATE_DIR/$(basename "$dir").state"
        if [[ -f "$state_file" ]]; then
            local last_sync=$(stat -c %Y "$state_file" 2>/dev/null || echo "0")
            echo "  - $dir (上次同步: $(date -d @$last_sync '+%Y-%m-%d %H:%M:%S'))"
        else
            echo "  - $dir (未同步)"
        fi
    done
    
    echo ""
    echo "冲突目录: $CONFLICT_DIR"
    local conflict_count=$(find "$CONFLICT_DIR" -name "CONFLICT_INFO.txt" 2>/dev/null | wc -l)
    echo "未解决冲突: $conflict_count"
    
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "守护进程: 运行中 (PID: $pid)"
        else
            echo "守护进程: 未运行"
            rm -f "$PID_FILE"
        fi
    else
        echo "守护进程: 未运行"
    fi
}

show_conflicts() {
    echo "========== 未解决的冲突 =========="
    
    local found=false
    for conflict_info in "$CONFLICT_DIR"/*/CONFLICT_INFO.txt; do
        if [[ -f "$conflict_info" ]]; then
            found=true
            echo ""
            echo "冲突: $(dirname "$conflict_info")"
            cat "$conflict_info"
        fi
    done
    
    if [[ "$found" == "false" ]]; then
        echo "没有未解决的冲突 ✓"
    fi
}

start_daemon() {
    if [[ -f "$PID_FILE" ]]; then
        local old_pid=$(cat "$PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            log_error "守护进程已在运行 (PID: $old_pid)"
            return 1
        fi
    fi
    
    log_info "启动同步守护进程..."
    
    # 后台运行
    (
        # 保存PID
        echo $$ > "$PID_FILE"
        
        # 首次同步
        scheduled_sync
        
        # 定时循环
        while true; do
            sleep "$SYNC_INTERVAL"
            scheduled_sync
        done
    ) &
    
    log_info "守护进程已启动 (PID: $!)"
}

stop_daemon() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            rm -f "$PID_FILE"
            log_info "守护进程已停止"
        else
            log_warn "守护进程未运行"
            rm -f "$PID_FILE"
        fi
    else
        log_warn "守护进程未运行"
    fi
}

test_connection() {
    echo "测试VM连接..."
    
    if check_vm_connection; then
        echo "✓ SSH连接成功"
        
        # 测试VM端目录
        if ssh $SSH_OPTS "$VM_USER@$VM_HOST" "test -d $VM_SYNC_DIR"; then
            echo "✓ VM同步目录存在: $VM_SYNC_DIR"
        else
            echo "✗ VM同步目录不存在: $VM_SYNC_DIR"
            echo "  正在创建..."
            ssh $SSH_OPTS "$VM_USER@$VM_HOST" "sudo mkdir -p $VM_SYNC_DIR && sudo chown $VM_USER:$VM_USER $VM_SYNC_DIR"
        fi
        
        # 测试rsync
        echo "测试rsync..."
        if rsync --dry-run $SSH_OPTS /dev/null "$VM_USER@$VM_HOST:/tmp/" &>/dev/null; then
            echo "✓ rsync可用"
        else
            echo "✗ rsync测试失败"
        fi
        
        return 0
    else
        echo "✗ 无法连接到VM"
        echo "  请检查SSH隧道: ssh -p $VM_PORT $VM_USER@$VM_HOST"
        return 1
    fi
}

# =============================================================================
# 主程序
# =============================================================================

main() {
    # 解析全局选项
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -c|--conflict)
                CONFLICT_STRATEGY="$2"
                shift 2
                ;;
            -i|--interval)
                SYNC_INTERVAL="$2"
                shift 2
                ;;
            -d|--debug)
                DEBUG=1
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done
    
    # 确保日志目录存在
    mkdir -p "$LOG_DIR"
    
    local command="${1:-help}"
    shift || true
    
    case "$command" in
        init)
            init
            ;;
        sync)
            init
            if [[ -n "${1:-}" ]]; then
                bidirectional_sync "$1"
            else
                scheduled_sync
            fi
            ;;
        push)
            init
            if [[ -n "${1:-}" ]]; then
                sync_to_vm "$1"
            else
                for dir in "${SYNC_DIRS[@]}"; do
                    sync_to_vm "$dir"
                done
            fi
            ;;
        pull)
            init
            if [[ -n "${1:-}" ]]; then
                sync_from_vm "$1"
            else
                for dir in "${SYNC_DIRS[@]}"; do
                    sync_from_vm "$dir"
                done
            fi
            ;;
        watch)
            init && watch_mode
            ;;
        daemon)
            init && start_daemon
            ;;
        stop)
            stop_daemon
            ;;
        status)
            show_status
            ;;
        conflicts)
            show_conflicts
            ;;
        test)
            test_connection
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主程序
main "$@"
