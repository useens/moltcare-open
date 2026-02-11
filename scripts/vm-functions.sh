#!/bin/bash
# VM快速协作函数库
# 在进化脚本中source此文件使用

# VM协作执行函数
vm_run() {
    local task_name="$1"
    shift
    local cmd="$@"
    
    echo "🔄 VM协作: $task_name"
    /root/.openclaw/workspace/scripts/vm-collaborate.sh "$task_name" "$cmd"
}

# 在VM上执行Python脚本
vm_python() {
    local script_name="$1"
    shift
    local args="$@"
    
    vm_run "Python: $script_name" "cd ~/.openclaw/workspace && python3 $script_name $args"
}

# 在VM上执行浏览器任务（资源隔离）
vm_browser() {
    local task_name="$1"
    shift
    local url="$1"
    
    vm_run "Browser: $task_name" "cd ~/.openclaw/workspace && python3 scripts/web-extractor/moltbook-super-extractor.py $url"
}

# 在VM上执行向量计算任务（CPU隔离）
vm_vector() {
    local task_name="$1"
    
    vm_run "Vector: $task_name" "cd ~/.openclaw/workspace && python3 scripts/vector-memory/batch_import.py"
}

# 检查VM是否可协作
vm_check() {
    ssh -p 4444 -o ConnectTimeout=3 -o StrictHostKeyChecking=no root@localhost 'echo VM_READY' 2>/dev/null | grep -q "VM_READY"
}

# 同步VM状态（轻量，不执行完整复活）
vm_sync_light() {
    echo "🔄 轻量同步VM..."
    ssh -p 4444 -o StrictHostKeyChecking=no root@localhost '
        cd ~/.openclaw/workspace && git pull origin master 2>/dev/null || git pull origin main 2>/dev/null
    '
}
