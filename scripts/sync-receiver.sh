#!/bin/bash
# =============================================================================
# 双节点数据双向同步系统 - VM端同步接收器
# 路径: /opt/linlin/sync-receiver.sh
# 功能: 接收主节点的同步请求，处理文件传输
# =============================================================================

set -euo pipefail

# =============================================================================
# 配置区域
# =============================================================================

# VM端工作目录
VM_WORKDIR="/opt/linlin/workspace"
SYNC_STATE_DIR="/opt/linlin/.sync-state"
LOG_DIR="/opt/linlin/logs"
LOG_FILE="$LOG_DIR/sync-receiver.log"
PID_FILE="/opt/linlin/sync-receiver.pid"

# 同步目录配置（与主节点保持一致）
SYNC_DIRS=(
    "memory"
    "scripts"
    # "credentials"  # 可选，默认不同步敏感数据
)

# 接收配置
UPLOAD_TMP="$VM_WORKDIR/.sync-tmp"
BATCH_SIZE=100
MAX_UPLOAD_SIZE="100M"  # 最大单次上传大小

# 安全设置
ALLOWED_HOSTS=("localhost" "127.0.0.1")  # 允许连接的主机
REQUIRE_AUTH=true                          # 是否需要认证
AUTH_TOKEN_FILE="/opt/linlin/.sync-auth"   # 认证令牌文件

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
# 初始化
# =============================================================================

init() {
    # 创建必要的目录
    mkdir -p "$VM_WORKDIR" "$SYNC_STATE_DIR" "$LOG_DIR" "$UPLOAD_TMP"
    
    for dir in "${SYNC_DIRS[@]}"; do
        mkdir -p "$VM_WORKDIR/$dir"
    done
    
    # 生成认证令牌（如果不存在）
    if [[ ! -f "$AUTH_TOKEN_FILE" ]]; then
        generate_auth_token
    fi
    
    log_info "VM同步接收器初始化完成"
    log_info "工作目录: $VM_WORKDIR"
}

generate_auth_token() {
    local token=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | xxd -p | tr -d '\n')
    echo "$token" > "$AUTH_TOKEN_FILE"
    chmod 600 "$AUTH_TOKEN_FILE"
    log_info "生成新的认证令牌"
}

get_auth_token() {
    if [[ -f "$AUTH_TOKEN_FILE" ]]; then
        cat "$AUTH_TOKEN_FILE"
    else
        echo ""
    fi
}

# =============================================================================
# 同步处理
# =============================================================================

handle_sync_request() {
    local action="$1"
    local dir="$2"
    shift 2
    
    case "$action" in
        "push")
            # 主节点推送到VM
            receive_files "$dir"
            ;;
        "pull")
            # 主节点从VM拉取
            send_files "$dir"
            ;;
        "status")
            # 返回同步状态
            get_sync_status "$dir"
            ;;
        "verify")
            # 验证文件完整性
            verify_files "$dir"
            ;;
        *)
            log_error "未知同步操作: $action"
            return 1
            ;;
    esac
}

receive_files() {
    local dir="$1"
    local target_path="$VM_WORKDIR/$dir"
    
    log_info "接收文件: $dir"
    
    # 确保目标目录存在
    mkdir -p "$target_path"
    
    # 创建接收临时目录
    local tmp_dir="$UPLOAD_TMP/receive_$(date +%s)_$$"
    mkdir -p "$tmp_dir"
    
    # 标准输入接收文件列表和校验信息
    local file_list="$tmp_dir/files.list"
    while IFS= read -r line; do
        [[ "$line" == "EOF" ]] && break
        echo "$line" >> "$file_list"
    done
    
    log_info "接收文件清单: $(wc -l < "$file_list" 2>/dev/null || echo 0) 个文件"
    
    # 使用rsync接收文件
    # 注意：实际文件传输由主节点的rsync直接处理
    # 这里主要用于记录和处理元数据
    
    # 更新同步状态
    update_sync_state "$dir"
    
    # 清理临时目录
    rm -rf "$tmp_dir"
    
    log_info "文件接收完成: $dir"
}

send_files() {
    local dir="$1"
    local source_path="$VM_WORKDIR/$dir"
    
    log_info "发送文件: $dir"
    
    if [[ ! -d "$source_path" ]]; then
        log_error "目录不存在: $source_path"
        return 1
    fi
    
    # 生成文件清单
    local file_list="$SYNC_STATE_DIR/$(basename "$dir").manifest"
    find "$source_path" -type f | while read -r file; do
        local rel_path="${file#$source_path/}"
        local checksum=$(md5sum "$file" 2>/dev/null | cut -d' ' -f1 || echo "")
        local size=$(stat -c%s "$file" 2>/dev/null || echo "0")
        local mtime=$(stat -c%Y "$file" 2>/dev/null || echo "0")
        echo "$rel_path|$checksum|$size|$mtime"
    done > "$file_list"
    
    # 输出清单到标准输出（供主节点读取）
    cat "$file_list"
    
    log_info "文件清单已发送: $(wc -l < "$file_list" 2>/dev/null || echo 0) 个文件"
}

update_sync_state() {
    local dir="$1"
    local state_file="$SYNC_STATE_DIR/$(basename "$dir").state"
    
    # 记录同步时间
    date +%s > "$state_file"
    
    # 生成文件校验清单
    local manifest_file="$SYNC_STATE_DIR/$(basename "$dir").manifest"
    find "$VM_WORKDIR/$dir" -type f -exec md5sum {} \; 2>/dev/null > "$manifest_file" || true
    
    log_debug "同步状态已更新: $dir"
}

get_sync_status() {
    local dir="${1:-all}"
    
    echo "{"
    echo "  \"timestamp\": $(date +%s),"
    echo "  \"hostname\": \"$(hostname)\","
    echo "  \"directories\": {"
    
    local first=true
    for d in "${SYNC_DIRS[@]}"; do
        [[ "$dir" != "all" && "$dir" != "$d" ]] && continue
        
        local state_file="$SYNC_STATE_DIR/$(basename "$d").state"
        local last_sync="0"
        [[ -f "$state_file" ]] && last_sync=$(cat "$state_file")
        
        local file_count=$(find "$VM_WORKDIR/$d" -type f 2>/dev/null | wc -l)
        local total_size=$(du -sb "$VM_WORKDIR/$d" 2>/dev/null | cut -f1 || echo "0")
        
        [[ "$first" == "true" ]] || echo ","
        first=false
        
        cat << EOF
    "$d": {
      "last_sync": $last_sync,
      "file_count": $file_count,
      "total_size": $total_size
    }
EOF
    done
    
    echo "  }"
    echo "}"
}

verify_files() {
    local dir="$1"
    local manifest_file="$SYNC_STATE_DIR/$(basename "$dir").manifest"
    
    log_info "验证文件完整性: $dir"
    
    if [[ ! -f "$manifest_file" ]]; then
        log_warn "无校验清单: $dir"
        return 1
    fi
    
    local errors=0
    while IFS= read -r line; do
        local checksum="${line%% *}"
        local file="${line#* }"
        
        if [[ ! -f "$file" ]]; then
            log_error "文件缺失: $file"
            ((errors++))
            continue
        fi
        
        local current_checksum=$(md5sum "$file" 2>/dev/null | cut -d' ' -f1)
        if [[ "$checksum" != "$current_checksum" ]]; then
            log_error "校验和不匹配: $file"
            ((errors++))
        fi
    done < "$manifest_file"
    
    if [[ $errors -eq 0 ]]; then
        log_info "文件验证通过: $dir"
        return 0
    else
        log_error "文件验证失败: $errors 个错误"
        return 1
    fi
}

# =============================================================================
# 命令处理（通过标准输入）
# =============================================================================

process_command() {
    local cmd_line="$1"
    local cmd=($cmd_line)
    
    case "${cmd[0]}" in
        "SYNC")
            # SYNC <action> <dir>
            handle_sync_request "${cmd[1]}" "${cmd[2]}"
            ;;
        "STATUS")
            # STATUS [dir]
            get_sync_status "${cmd[1]:-all}"
            ;;
        "VERIFY")
            # VERIFY <dir>
            verify_files "${cmd[1]}"
            ;;
        "PING")
            echo "PONG"
            ;;
        *)
            log_error "未知命令: ${cmd[0]}"
            echo "ERROR: Unknown command"
            return 1
            ;;
    esac
}

# =============================================================================
# 网络服务模式（通过socat或nc）
# =============================================================================

start_server() {
    local port="${1:-22222}"
    
    log_info "启动同步接收服务器，端口: $port"
    
    # 检查端口占用
    if ss -tlnp | grep -q ":$port "; then
        log_error "端口 $port 已被占用"
        return 1
    fi
    
    # 保存PID
    echo $$ > "$PID_FILE"
    
    # 使用socat启动服务（如果可用）
    if command -v socat &>/dev/null; then
        socat TCP-LISTEN:$port,fork,reuseaddr EXEC:"$0 handle-connection"
    else
        # 降级方案：使用nc
        log_warn "socat 未安装，使用 nc 作为降级方案"
        while true; do
            nc -l -p "$port" -c "$0 handle-connection" 2>&1 || true
        done
    fi
}

handle_connection() {
    # 读取命令
    local cmd_line
    IFS= read -r cmd_line
    
    log_debug "收到命令: $cmd_line"
    
    # 处理命令
    process_command "$cmd_line"
}

# =============================================================================
# 系统服务集成
# =============================================================================

install_service() {
    log_info "安装系统服务..."
    
    # 创建systemd服务文件
    local service_file="/etc/systemd/system/linlin-sync-receiver.service"
    
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=LinLin Sync Receiver
After=network.target

[Service]
Type=simple
User=linlin
Group=linlin
WorkingDirectory=/opt/linlin
ExecStart=/opt/linlin/sync-receiver.sh server 22222
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable linlin-sync-receiver
    
    log_info "服务已安装: linlin-sync-receiver"
    log_info "启动服务: sudo systemctl start linlin-sync-receiver"
}

uninstall_service() {
    log_info "卸载系统服务..."
    sudo systemctl stop linlin-sync-receiver 2>/dev/null || true
    sudo systemctl disable linlin-sync-receiver 2>/dev/null || true
    sudo rm -f /etc/systemd/system/linlin-sync-receiver.service
    sudo systemctl daemon-reload
    log_info "服务已卸载"
}

# =============================================================================
# 命令行接口
# =============================================================================

show_help() {
    cat << EOF
VM端同步接收器

用法: $(basename "$0") [命令] [选项]

命令:
    init                    初始化接收器
    server [port]           启动网络服务（默认端口22222）
    handle-connection       处理单个连接（内部使用）
    status [dir]            查看同步状态
    verify <dir>            验证文件完整性
    install-service         安装为系统服务
    uninstall-service       卸载系统服务
    token                   显示/重新生成认证令牌
    test                    测试接收器功能
    help                    显示帮助

作为SSH强制命令使用:
    在 authorized_keys 中添加:
    command="/opt/linlin/sync-receiver.sh handle-connection",no-pty,no-port-forwarding ssh-rsa AAAA...

示例:
    # 初始化
    $(basename "$0") init

    # 启动服务
    $(basename "$0") server 22222

    # 查看状态
    $(basename "$0") status
EOF
}

test_receiver() {
    log_info "测试同步接收器..."
    
    # 测试目录结构
    echo "1. 检查目录结构..."
    for dir in "$VM_WORKDIR" "$SYNC_STATE_DIR" "$LOG_DIR"; do
        if [[ -d "$dir" ]]; then
            echo "   ✓ $dir"
        else
            echo "   ✗ $dir 不存在"
        fi
    done
    
    # 测试同步目录
    echo ""
    echo "2. 检查同步目录..."
    for dir in "${SYNC_DIRS[@]}"; do
        if [[ -d "$VM_WORKDIR/$dir" ]]; then
            local count=$(find "$VM_WORKDIR/$dir" -type f 2>/dev/null | wc -l)
            echo "   ✓ $dir ($count 个文件)"
        else
            echo "   ✗ $dir 不存在"
        fi
    done
    
    # 测试命令处理
    echo ""
    echo "3. 测试命令处理..."
    local result=$(echo "PING" | $0 handle-connection)
    if [[ "$result" == "PONG" ]]; then
        echo "   ✓ PING/PONG 测试通过"
    else
        echo "   ✗ PING/PONG 测试失败"
    fi
    
    # 测试状态查询
    echo ""
    echo "4. 测试状态查询..."
    if $0 status memory >/dev/null 2>&1; then
        echo "   ✓ 状态查询正常"
    else
        echo "   ✗ 状态查询失败"
    fi
    
    log_info "测试完成"
}

# =============================================================================
# 主程序
# =============================================================================

main() {
    local command="${1:-help}"
    shift || true
    
    case "$command" in
        init)
            init
            ;;
        server)
            init
            start_server "${1:-22222}"
            ;;
        handle-connection)
            # 从标准输入读取并处理
            while IFS= read -r line; do
                process_command "$line"
            done
            ;;
        status)
            get_sync_status "${1:-all}"
            ;;
        verify)
            if [[ -n "${1:-}" ]]; then
                verify_files "$1"
            else
                for dir in "${SYNC_DIRS[@]}"; do
                    verify_files "$dir"
                done
            fi
            ;;
        install-service)
            install_service
            ;;
        uninstall-service)
            uninstall_service
            ;;
        token)
            if [[ "${1:-}" == "--regenerate" ]]; then
                generate_auth_token
            fi
            echo "认证令牌: $(get_auth_token)"
            ;;
        test)
            test_receiver
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
