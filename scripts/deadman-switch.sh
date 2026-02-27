#!/bin/bash
# deadman-switch.sh - 死手开关系统 v1.0
# 每3小时检测森森状态，无响应则自动回滚

WORKSPACE="/root/.openclaw/workspace"
SNAPSHOT_DIR="$WORKSPACE/.snapshots"
LOG_FILE="$WORKSPACE/logs/deadman-switch.log"
HEARTBEAT_TIMEOUT=300  # 5分钟超时
MAX_RETRIES=3

# 确保目录存在
mkdir -p "$SNAPSHOT_DIR" "$WORKSPACE/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 创建状态快照
save_snapshot() {
    local snapshot_id="snapshot_$(date +%Y%m%d_%H%M%S)"
    local snapshot_path="$SNAPSHOT_DIR/$snapshot_id"
    
    log "💾 创建状态快照: $snapshot_id"
    
    mkdir -p "$snapshot_path"
    
    # 保存核心记忆文件
    cp -r "$WORKSPACE/memory" "$snapshot_path/" 2>/dev/null || true
    cp "$WORKSPACE/MEMORY.md" "$snapshot_path/" 2>/dev/null || true
    cp "$WORKSPACE/USER.md" "$snapshot_path/" 2>/dev/null || true
    cp "$WORKSPACE/SOUL.md" "$snapshot_path/" 2>/dev/null || true
    cp "$WORKSPACE/AGENTS.md" "$snapshot_path/" 2>/dev/null || true
    cp "$WORKSPACE/IDENTITY.md" "$snapshot_path/" 2>/dev/null || true
    
    # 保存向量记忆
    cp -r "$WORKSPACE/memory/vector" "$snapshot_path/" 2>/dev/null || true
    
    # 保存配置文件
    cp -r "$WORKSPACE/config" "$snapshot_path/" 2>/dev/null || true
    
    # 创建快照元数据
    cat > "$snapshot_path/meta.json" << EOF
{
    "id": "$snapshot_id",
    "timestamp": "$(date -Iseconds)",
    "unix_time": $(date +%s),
    "files_count": $(find "$snapshot_path" -type f | wc -l)
}
EOF
    
    # 压缩快照
    cd "$SNAPSHOT_DIR"
    tar -czf "${snapshot_id}.tar.gz" "$snapshot_id"
    rm -rf "$snapshot_path"
    
    log "✅ 快照已保存: ${snapshot_id}.tar.gz"
    
    # 清理旧快照（只保留最近3个）
    ls -t "$SNAPSHOT_DIR"/snapshot_*.tar.gz 2>/dev/null | tail -n +4 | xargs -r rm -f
    
    echo "$snapshot_id"
}

# 发送心跳检测
send_heartbeat() {
    log "💓 发送心跳检测..."
    
    # 通过多种方式检测
    
    # 方式1: 检查OpenClaw网关状态
    if command -v openclaw &> /dev/null; then
        if openclaw gateway status &> /dev/null; then
            log "✅ 网关状态正常"
            return 0
        fi
    fi
    
    # 方式2: 检查关键进程
    if pgrep -f "openclaw" > /dev/null; then
        log "✅ OpenClaw进程运行中"
        return 0
    fi
    
    # 方式3: 检查最近日志活动
    local last_log="$WORKSPACE/logs/deadman-switch.log"
    if [ -f "$last_log" ]; then
        local last_modified=$(stat -c %Y "$last_log" 2>/dev/null || stat -f %m "$last_log" 2>/dev/null)
        local now=$(date +%s)
        local diff=$((now - last_modified))
        
        if [ $diff -lt 3600 ]; then
            log "✅ 近期有活动记录 (${diff}秒前)"
            return 0
        fi
    fi
    
    log "❌ 心跳检测失败"
    return 1
}

# 执行回滚
rollback_to_snapshot() {
    local target_snapshot="$1"
    
    log "🚨 触发回滚机制！恢复到: $target_snapshot"
    
    # 发送紧急通知
    local alert_msg="🚨 死手开关触发\n森森未响应心跳检测\n正在自动回滚到: $target_snapshot\n时间: $(date)"
    
    # 尝试多种通知方式
    if command -v openclaw &> /dev/null; then
        openclaw notify "$alert_msg" 2>/dev/null || true
    fi
    
    # 如果提供了具体快照，恢复到该快照
    if [ -n "$target_snapshot" ] && [ -f "$SNAPSHOT_DIR/${target_snapshot}.tar.gz" ]; then
        log "📦 正在恢复快照..."
        
        # 创建当前状态备份（以防万一）
        local emergency_backup="$SNAPSHOT_DIR/emergency_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar -czf "$emergency_backup" -C "$WORKSPACE" memory MEMORY.md USER.md SOUL.md 2>/dev/null || true
        log "💾 紧急备份已创建: $emergency_backup"
        
        # 解压快照
        cd "$WORKSPACE"
        tar -xzf "$SNAPSHOT_DIR/${target_snapshot}.tar.gz"
        
        # 恢复文件
        if [ -d "$SNAPSHOT_DIR/$target_snapshot/memory" ]; then
            rm -rf "$WORKSPACE/memory"
            cp -r "$SNAPSHOT_DIR/$target_snapshot/memory" "$WORKSPACE/"
        fi
        
        for file in MEMORY.md USER.md SOUL.md AGENTS.md IDENTITY.md; do
            if [ -f "$SNAPSHOT_DIR/$target_snapshot/$file" ]; then
                cp "$SNAPSHOT_DIR/$target_snapshot/$file" "$WORKSPACE/"
            fi
        done
        
        # 恢复配置
        if [ -d "$SNAPSHOT_DIR/$target_snapshot/config" ]; then
            rm -rf "$WORKSPACE/config"
            cp -r "$SNAPSHOT_DIR/$target_snapshot/config" "$WORKSPACE/"
        fi
        
        log "✅ 回滚完成！已恢复到: $target_snapshot"
        
        # 记录回滚事件
        cat >> "$WORKSPACE/logs/rollback-history.log" << EOF
[$(date '+%Y-%m-%d %H:%M:%S')] 回滚执行
- 触发原因: 心跳检测失败
- 恢复快照: $target_snapshot
- 紧急备份: $emergency_backup
EOF
        
        # 重启服务（如果需要）
        if command -v openclaw &> /dev/null; then
            log "🔄 尝试重启OpenClaw服务..."
            openclaw gateway restart 2>/dev/null || true
        fi
        
        return 0
    else
        log "❌ 未找到指定快照，使用最新可用快照"
        
        # 使用最新的快照
        local latest=$(ls -t "$SNAPSHOT_DIR"/snapshot_*.tar.gz 2>/dev/null | head -1)
        if [ -n "$latest" ]; then
            local snap_name=$(basename "$latest" .tar.gz)
            rollback_to_snapshot "$snap_name"
        else
            log "❌ 错误: 没有可用的快照！"
            return 1
        fi
    fi
}

# 主执行流程
main() {
    log "=== 死手开关检测开始 ==="
    
    # 步骤1: 保存当前状态
    local current_snapshot=$(save_snapshot)
    
    # 步骤2: 等待3小时前的快照（用于回滚）
    local target_rollback=""
    local cutoff_time=$(($(date +%s) - 10800))  # 3小时前
    
    for snap in "$SNAPSHOT_DIR"/snapshot_*.tar.gz; do
        if [ -f "$snap" ]; then
            local snap_name=$(basename "$snap" .tar.gz)
            local snap_time=$(echo "$snap_name" | sed 's/snapshot_//; s/_/ /')
            local snap_unix=$(date -d "$snap_time" +%s 2>/dev/null || date -j -f "%Y%m%d %H%M%S" "$snap_time" +%s 2>/dev/null)
            
            if [ -n "$snap_unix" ] && [ "$snap_unix" -le "$cutoff_time" ]; then
                target_rollback="$snap_name"
                break
            fi
        fi
    done
    
    if [ -z "$target_rollback" ]; then
        log "⚠️ 未找到3小时前的快照，将使用最早的可用快照"
        target_rollback=$(ls -t "$SNAPSHOT_DIR"/snapshot_*.tar.gz 2>/dev/null | tail -1 | xargs basename | sed 's/.tar.gz//')
    fi
    
    log "🎯 回滚目标已确定: $target_rollback"
    
    # 步骤3: 发送心跳检测
    local retry_count=0
    local heartbeat_success=false
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if send_heartbeat; then
            heartbeat_success=true
            break
        fi
        
        retry_count=$((retry_count + 1))
        log "⚠️ 心跳检测失败，重试 $retry_count/$MAX_RETRIES..."
        sleep 10
    done
    
    # 步骤4: 根据心跳结果执行操作
    if [ "$heartbeat_success" = true ]; then
        log "✅ 心跳检测通过，系统运行正常"
        log "💾 当前快照已保存: $current_snapshot"
        log "🎯 如需回滚将使用: $target_rollback"
    else
        log "🚨 心跳检测连续失败 $MAX_RETRIES 次！"
        rollback_to_snapshot "$target_rollback"
    fi
    
    log "=== 检测结束 ==="
}

# 执行
main "$@"
