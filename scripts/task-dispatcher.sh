#!/bin/bash
#
# 任务分发器 - 主节点 (云端)
# 路径: scripts/task-dispatcher.sh
# 功能: 检测VM状态，智能分发任务到VM或本地执行
#

set -euo pipefail

# ==================== 配置 ====================
VM_HOST="user-virtual-machine"
VM_PORT="4444"
VM_USER="root"
SSH_KEY="/tmp/linlin_cloud_key"
VM_EXECUTOR="/opt/linlin/task-executor.sh"
LOCAL_EXECUTOR="/opt/linlin/task-executor.sh"

# 任务队列目录
TASK_QUEUE_DIR="${TASK_QUEUE_DIR:-/var/run/linlin/tasks}"
TASK_RESULTS_DIR="${TASK_RESULTS_DIR:-/var/run/linlin/results}"

# 日志
LOG_FILE="${LOG_FILE:-/var/log/linlin/task-dispatcher.log}"

# ==================== 日志函数 ====================
log() {
    local level="$1"
    shift
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*"
    echo "$msg" | tee -a "$LOG_FILE" 2>/dev/null || echo "$msg"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_debug() { [[ "${DEBUG:-0}" == "1" ]] && log "DEBUG" "$@"; }

# ==================== 初始化 ====================
init() {
    mkdir -p "$TASK_QUEUE_DIR" "$TASK_RESULTS_DIR" "$(dirname "$LOG_FILE")"
    log_info "任务分发器初始化完成"
}

# ==================== VM状态检测 ====================
check_vm_online() {
    log_debug "检测VM在线状态..."
    
    # 检测SSH连接和VM执行器是否存在
    if ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no \
           -i "$SSH_KEY" -p "$VM_PORT" "$VM_USER@$VM_HOST" \
           "test -x $VM_EXECUTOR" 2>/dev/null; then
        log_debug "VM在线且执行器可用"
        return 0
    else
        log_warn "VM离线或执行器不可用"
        return 1
    fi
}

# ==================== SSH执行封装 ====================
vm_exec() {
    local cmd="$1"
    ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
        -i "$SSH_KEY" -p "$VM_PORT" "$VM_USER@$VM_HOST" \
        "$cmd" 2>/dev/null
}

# ==================== 任务分发 ====================
dispatch_task() {
    local task_type="$1"
    local task_id="${2:-$(date +%s%N | cut -b1-13)}"
    local task_payload="${3:-}"
    local task_script="${4:-}"
    
    log_info "分发任务 [ID: $task_id, Type: $task_type]"
    
    local result_file="$TASK_RESULTS_DIR/${task_id}.json"
    local vm_online=false
    
    # 检测VM状态
    if check_vm_online; then
        vm_online=true
    fi
    
    case "$task_type" in
        "lightweight")
            # 轻量级任务：单节点执行，优先VM
            if [[ "$vm_online" == "true" ]]; then
                log_info "轻量级任务 → VM执行"
                _exec_on_vm "$task_id" "$task_payload" "$task_script" > "$result_file.vm" 2>&1
                _format_result "$task_id" "vm" "$?" "$result_file.vm" > "$result_file"
                rm -f "$result_file.vm"
            else
                log_info "轻量级任务 → 本地执行 (VM离线)"
                _exec_local "$task_id" "$task_payload" "$task_script" > "$result_file.local" 2>&1
                _format_result "$task_id" "local" "$?" "$result_file.local" > "$result_file"
                rm -f "$result_file.local"
            fi
            ;;
            
        "parallel")
            # 并行任务：主节点和VM同时执行，结果合并
            log_info "并行任务 → 双节点并发执行"
            
            # 本地执行（后台）
            _exec_local "$task_id-local" "$task_payload" "$task_script" > "$result_file.local" 2>&1 &
            local local_pid=$!
            
            # VM执行（后台，如果在线）
            local vm_pid=""
            if [[ "$vm_online" == "true" ]]; then
                _exec_on_vm "$task_id-vm" "$task_payload" "$task_script" > "$result_file.vm" 2>&1 &
                vm_pid=$!
            fi
            
            # 等待本地完成
            wait $local_pid
            local local_exit=$?
            
            # 等待VM完成（如果在执行）
            local vm_exit=127
            if [[ -n "$vm_pid" ]]; then
                wait $vm_pid
                vm_exit=$?
            fi
            
            # 合并结果
            _merge_parallel_results "$task_id" "$result_file.local" "$local_exit" \
                                   "$result_file.vm" "$vm_exit" "$vm_online" > "$result_file"
            
            # 清理临时文件
            rm -f "$result_file.local" "$result_file.vm"
            ;;
            
        "vm-only")
            # VM专用任务：必须在VM执行
            if [[ "$vm_online" != "true" ]]; then
                log_error "VM专用任务无法执行 - VM离线 [TaskID: $task_id]"
                _format_result "$task_id" "failed" 1 "" "VM离线，VM专用任务无法执行" > "$result_file"
                return 1
            fi
            
            log_info "VM专用任务 → VM执行"
            _exec_on_vm "$task_id" "$task_payload" "$task_script" > "$result_file.vm" 2>&1
            _format_result "$task_id" "vm" "$?" "$result_file.vm" > "$result_file"
            rm -f "$result_file.vm"
            ;;
            
        *)
            log_error "未知任务类型: $task_type"
            return 1
            ;;
    esac
    
    log_info "任务完成 [ID: $task_id] → $result_file"
    cat "$result_file"
}

# ==================== 任务执行封装 ====================
_exec_local() {
    local task_id="$1"
    local payload="$2"
    local script="$3"
    
    export TASK_ID="$task_id"
    export TASK_NODE="local"
    export TASK_PAYLOAD="$payload"
    
    if [[ -n "$script" && -f "$script" ]]; then
        bash "$script"
    elif [[ -n "$payload" ]]; then
        eval "$payload"
    else
        echo "错误：未提供任务脚本或payload"
        return 1
    fi
}

_exec_on_vm() {
    local task_id="$1"
    local payload="$2"
    local script="$3"
    
    # 构建远程命令
    local remote_cmd="export TASK_ID='$task_id'; export TASK_NODE='vm'; export TASK_PAYLOAD='$payload';"
    
    if [[ -n "$script" ]]; then
        # 将脚本内容传输到VM执行
        local script_content
        script_content=$(cat "$script" | base64 -w0)
        remote_cmd="$remote_cmd echo '$script_content' | base64 -d | bash"
    elif [[ -n "$payload" ]]; then
        remote_cmd="$remote_cmd $payload"
    else
        echo "错误：未提供任务脚本或payload"
        return 1
    fi
    
    vm_exec "$remote_cmd"
}

# ==================== 结果格式化 ====================
_format_result() {
    local task_id="$1"
    local node="$2"
    local exit_code="$3"
    local output_file="$4"
    local error_msg="${5:-}"
    
    local output=""
    if [[ -f "$output_file" ]]; then
        output=$(cat "$output_file" | sed 's/"/\\"/g' | tr '\n' ' ')
    fi
    
    local status="success"
    [[ "$exit_code" -ne 0 ]] && status="failed"
    
    cat <<EOF
{
  "task_id": "$task_id",
  "timestamp": $(date +%s),
  "status": "$status",
  "node": "$node",
  "exit_code": $exit_code,
  "output": "$output",
  "error": "$error_msg"
}
EOF
}

_merge_parallel_results() {
    local task_id="$1"
    local local_file="$2"
    local local_exit="$3"
    local vm_file="$4"
    local vm_exit="$5"
    local vm_online="$6"
    
    local local_output=""
    local vm_output=""
    
    [[ -f "$local_file" ]] && local_output=$(cat "$local_file" | sed 's/"/\\"/g' | tr '\n' ' ')
    [[ -f "$vm_file" ]] && vm_output=$(cat "$vm_file" | sed 's/"/\\"/g' | tr '\n' ' ')
    
    local overall_status="success"
    [[ "$local_exit" -ne 0 ]] && overall_status="partial"
    [[ "$vm_online" == "true" && "$vm_exit" -ne 0 ]] && overall_status="partial"
    [[ "$local_exit" -ne 0 && ("$vm_online" != "true" || "$vm_exit" -ne 0) ]] && overall_status="failed"
    
    cat <<EOF
{
  "task_id": "$task_id",
  "timestamp": $(date +%s),
  "status": "$overall_status",
  "type": "parallel",
  "results": {
    "local": {
      "exit_code": $local_exit,
      "output": "$local_output"
    },
    "vm": {
      "exit_code": $vm_exit,
      "output": "$vm_output",
      "online": $vm_online
    }
  }
}
EOF
}

# ==================== 批量任务处理 ====================
process_batch() {
    local batch_file="$1"
    local max_parallel="${2:-4}"
    
    log_info "开始批量处理: $batch_file (最大并行: $max_parallel)"
    
    local pids=()
    local count=0
    
    while IFS= read -r line; do
        # 跳过注释和空行
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        
        # 解析任务: type|task_id|payload|script
        IFS='|' read -r task_type task_id payload script <<< "$line"
        
        # 后台执行
        dispatch_task "$task_type" "$task_id" "$payload" "$script" &
        pids+=($!)
        ((count++))
        
        # 控制并发数
        if [[ ${#pids[@]} -ge $max_parallel ]]; then
            wait "${pids[0]}"
            pids=("${pids[@]:1}")
        fi
    done < "$batch_file"
    
    # 等待所有任务完成
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
    
    log_info "批量处理完成: $count 个任务"
}

# ==================== 子代理管理 ====================
spawn_subagent() {
    local node="$1"  # "local" 或 "vm"
    local task_def="$2"
    
    log_info "在 $node 上生成子代理"
    
    if [[ "$node" == "vm" ]]; then
        if ! check_vm_online; then
            log_warn "VM离线，子代理回退到本地"
            node="local"
        fi
    fi
    
    local subagent_id="subagent-$(date +%s%N | cut -b1-13)-$RANDOM"
    
    if [[ "$node" == "vm" ]]; then
        # 在VM上生成子代理
        vm_exec "export SUBAGENT_ID='$subagent_id'; export TASK_DEF='$task_def'; nohup bash -c '
            echo \"子代理 $SUBAGENT_ID 启动\" >> /var/log/linlin/subagents.log
            # 子代理执行逻辑
            eval \"\$TASK_DEF\"
            echo \"子代理 \$SUBAGENT_ID 完成\" >> /var/log/linlin/subagents.log
        ' > /dev/null 2>&1 &"
    else
        # 在本地生成子代理
        (
            export SUBAGENT_ID="$subagent_id"
            export TASK_DEF="$task_def"
            nohup bash -c '
                echo "子代理 $SUBAGENT_ID 启动" >> /var/log/linlin/subagents.log
                eval "$TASK_DEF"
                echo "子代理 $SUBAGENT_ID 完成" >> /var/log/linlin/subagents.log
            ' > /dev/null 2>&1 &
        )
    fi
    
    echo "$subagent_id"
}

# ==================== 主入口 ====================
main() {
    init
    
    case "${1:-help}" in
        "dispatch")
            # 单任务分发: dispatch <type> <task_id> <payload> [script]
            shift
            dispatch_task "$@"
            ;;
        "batch")
            # 批量处理: batch <file> [max_parallel]
            shift
            process_batch "$@"
            ;;
        "status")
            # 检测VM状态
            if check_vm_online; then
                echo "VM状态: 在线"
                exit 0
            else
                echo "VM状态: 离线"
                exit 1
            fi
            ;;
        "subagent")
            # 生成子代理: subagent <local|vm> <task_def>
            shift
            spawn_subagent "$@"
            ;;
        "help"|*)
            cat <<EOF
任务分发器 - 双节点任务自动分发系统

用法:
  $0 dispatch <type> <task_id> <payload> [script]  分发单个任务
  $0 batch <file> [max_parallel]                  批量处理任务
  $0 status                                       检测VM状态
  $0 subagent <local|vm> <task_def>               生成子代理

任务类型:
  lightweight  - 轻量级任务，单节点执行，优先VM
  parallel     - 并行任务，双节点同时执行
  vm-only      - VM专用任务，必须在VM执行

示例:
  $0 dispatch lightweight task-001 'echo hello'
  $0 dispatch parallel task-002 '' ./scripts/test.sh
  $0 dispatch vm-only task-003 '' ./scripts/monitor.sh
  $0 batch tasks.txt 4

批量任务文件格式 (每行一个任务，用|分隔):
  lightweight|task-001|echo hello|
  parallel|task-002||/path/to/script.sh
  vm-only|task-003||/opt/linlin/monitor.sh
EOF
            ;;
    esac
}

main "$@"
