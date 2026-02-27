#!/bin/bash
# deadman-switch-v2.sh - 死手开关系统 v2.0
# 增强版: 增量备份 + 深度健康检测 + 主动通知 + 回滚验证

WORKSPACE="/root/.openclaw/workspace"
SNAPSHOT_DIR="$WORKSPACE/.snapshots"
LOG_FILE="$WORKSPACE/logs/deadman-switch.log"
HEALTH_SCORE_FILE="$WORKSPACE/.snapshots/health-score.json"
MAX_RETRIES=3
HEALTH_THRESHOLD=60  # 健康分低于此值触发回滚

# 确保目录存在
mkdir -p "$SNAPSHOT_DIR/memory-changes" "$WORKSPACE/logs" "$WORKSPACE/.state"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ============================================
# 1. 智能增量备份系统
# ============================================

save_incremental_snapshot() {
    local snapshot_id="snapshot_$(date +%Y%m%d_%H%M%S)"
    local snapshot_path="$SNAPSHOT_DIR/$snapshot_id"
    local manifest_file="$SNAPSHOT_DIR/manifest.json"
    
    log "💾 创建增量快照: $snapshot_id"
    
    mkdir -p "$snapshot_path"
    
    # 使用rsync的--link-dest实现硬链接增量（如果支持）
    local last_snapshot=$(ls -td "$SNAPSHOT_DIR"/snapshot_*/ 2>/dev/null | head -1)
    
    # 计算文件哈希，只备份变化的文件
    local changed_files=0
    local total_size=0
    
    # 备份核心文件（这些通常较小，全量备份）
    for file in MEMORY.md USER.md SOUL.md AGENTS.md IDENTITY.md HEARTBEAT.md TOOLS.md; do
        if [ -f "$WORKSPACE/$file" ]; then
            cp "$WORKSPACE/$file" "$snapshot_path/"
            ((changed_files++))
            total_size=$((total_size + $(stat -c%s "$WORKSPACE/$file" 2>/dev/null || stat -f%z "$WORKSPACE/$file" 2>/dev/null)))
        fi
    done
    
    # 对于memory目录，使用文件级增量
    if [ -d "$WORKSPACE/memory" ]; then
        mkdir -p "$snapshot_path/memory"
        
        # 遍历memory目录，只复制修改过的文件
        while IFS= read -r -d '' file; do
            local rel_path="${file#$WORKSPACE/memory/}"
            local target_file="$snapshot_path/memory/$rel_path"
            local target_dir=$(dirname "$target_file")
            
            mkdir -p "$target_dir"
            
            # 检查文件是否变化（比较修改时间或哈希）
            local should_copy=false
            if [ -n "$last_snapshot" ] && [ -f "$last_snapshot/memory/$rel_path" ]; then
                if [ "$file" -nt "$last_snapshot/memory/$rel_path" ]; then
                    should_copy=true
                fi
            else
                should_copy=true
            fi
            
            if [ "$should_copy" = true ]; then
                cp "$file" "$target_file"
                ((changed_files++))
            else
                # 创建硬链接节省空间
                ln "$last_snapshot/memory/$rel_path" "$target_file" 2>/dev/null || cp "$file" "$target_file"
            fi
        done < <(find "$WORKSPACE/memory" -type f -print0 2>/dev/null)
    fi
    
    # 备份配置（通常很小，全量备份）
    if [ -d "$WORKSPACE/config" ]; then
        cp -r "$WORKSPACE/config" "$snapshot_path/"
    fi
    
    # 创建快照元数据
    local memory_usage=$(du -sm "$WORKSPACE/memory" 2>/dev/null | cut -f1)
    cat > "$snapshot_path/meta.json" << EOF
{
    "id": "$snapshot_id",
    "timestamp": "$(date -Iseconds)",
    "unix_time": $(date +%s),
    "changed_files": $changed_files,
    "memory_usage_mb": $memory_usage,
    "incremental": true,
    "base_snapshot": "$(basename "$last_snapshot" 2>/dev/null || echo 'none')"
}
EOF
    
    # 压缩快照
    cd "$SNAPSHOT_DIR"
    tar -czf "${snapshot_id}.tar.gz" "$snapshot_id" 2>/dev/null || true
    local compressed_size=$(stat -c%s "${snapshot_id}.tar.gz" 2>/dev/null || stat -f%z "${snapshot_id}.tar.gz" 2>/dev/null)
    
    rm -rf "$snapshot_path"
    
    log "✅ 增量快照完成: ${snapshot_id}.tar.gz (${compressed_size} bytes, ${changed_files} files changed)"
    
    # 更新manifest
    update_manifest "$snapshot_id"
    
    # 清理旧快照（智能保留策略）
    cleanup_old_snapshots
    
    echo "$snapshot_id"
}

update_manifest() {
    local new_snapshot="$1"
    local manifest_file="$SNAPSHOT_DIR/manifest.json"
    
    # 创建或更新manifest
    if [ -f "$manifest_file" ]; then
        # 添加新条目到manifest
        local temp_manifest=$(mktemp)
        jq --arg id "$new_snapshot" --arg time "$(date -Iseconds)" \
           '.snapshots += [{"id": $id, "timestamp": $time}] | .snapshots = .snapshots[-10:]' \
           "$manifest_file" > "$temp_manifest" 2>/dev/null || echo "{\"snapshots\": [{\"id\": \"$new_snapshot\", \"timestamp\": \"$(date -Iseconds)\"}]}" > "$temp_manifest"
        mv "$temp_manifest" "$manifest_file"
    else
        echo "{\"snapshots\": [{\"id\": \"$new_snapshot\", \"timestamp\": \"$(date -Iseconds)\"}]}" > "$manifest_file"
    fi
}

cleanup_old_snapshots() {
    # 智能清理策略：保留最近3个 + 每6小时一个 + 每天一个（7天）
    
    # 1. 保留最近3个
    local recent=$(ls -t "$SNAPSHOT_DIR"/snapshot_*.tar.gz 2>/dev/null | head -3)
    
    # 2. 每6小时保留一个（12:00, 18:00, 00:00, 06:00）
    local hourly_keep=""
    for hour in 00 06 12 18; do
        local match=$(ls -1 "$SNAPSHOT_DIR"/snapshot_*_${hour}00*.tar.gz 2>/dev/null | tail -1)
        if [ -n "$match" ]; then
            hourly_keep="$hourly_keep\n$match"
        fi
    done
    
    # 合并保留列表
    local keep_list=$(echo -e "$recent\n$hourly_keep" | sort -u)
    
    # 删除不在保留列表中的快照（保留7天内）
    for snap in "$SNAPSHOT_DIR"/snapshot_*.tar.gz; do
        local snap_name=$(basename "$snap")
        if ! echo "$keep_list" | grep -q "$snap_name"; then
            local snap_age_days=$(( ($(date +%s) - $(stat -c%Y "$snap" 2>/dev/null || stat -f%m "$snap" 2>/dev/null)) / 86400 ))
            if [ "$snap_age_days" -gt 7 ]; then
                rm -f "$snap"
                log "🗑️ 清理旧快照: $snap_name (age: ${snap_age_days} days)"
            fi
        fi
    done
}

# ============================================
# 2. 深度健康检测系统
# ============================================

calculate_health_score() {
    local score=100
    local checks_passed=0
    local total_checks=6
    local details=""
    
    # 检查1: OpenClaw网关响应 (25分)
    log "🔍 深度健康检测开始..."
    if command -v openclaw &> /dev/null; then
        if timeout 10 openclaw gateway status &> /dev/null; then
            score=$((score + 0))
            ((checks_passed++))
            details="$details\n  ✅ 网关响应正常 (+0, 基线)"
        else
            score=$((score - 25))
            details="$details\n  ❌ 网关无响应 (-25)"
        fi
    else
        score=$((score - 25))
        details="$details\n  ⚠️ OpenClaw命令不可用 (-25)"
    fi
    
    # 检查2: 进程存活 (20分)
    if pgrep -f "openclaw" > /dev/null; then
        local process_count=$(pgrep -f "openclaw" | wc -l)
        if [ "$process_count" -ge 2 ]; then
            ((checks_passed++))
            details="$details\n  ✅ 进程运行正常 ($process_count processes)"
        else
            score=$((score - 10))
            details="$details\n  ⚠️ 进程数量偏少 (-10)"
        fi
    else
        score=$((score - 20))
        details="$details\n  ❌ 进程未运行 (-20)"
    fi
    
    # 检查3: 内存状态 (15分)
    local memory_health=true
    if [ -f "$WORKSPACE/memory/vector/index.faiss" ]; then
        local index_size=$(stat -c%s "$WORKSPACE/memory/vector/index.faiss" 2>/dev/null || echo 0)
        if [ "$index_size" -gt 1000 ]; then
            ((checks_passed++))
            details="$details\n  ✅ 向量记忆索引正常 ($(numfmt --to=iec $index_size 2>/dev/null || echo ${index_size}b))"
        else
            score=$((score - 15))
            memory_health=false
            details="$details\n  ⚠️ 向量记忆索引异常 (-15)"
        fi
    fi
    
    # 检查4: 核心文件完整性 (15分)
    local core_files_ok=true
    for file in MEMORY.md USER.md SOUL.md; do
        if [ ! -f "$WORKSPACE/$file" ]; then
            core_files_ok=false
            break
        fi
    done
    if [ "$core_files_ok" = true ]; then
        ((checks_passed++))
        details="$details\n  ✅ 核心文件完整"
    else
        score=$((score - 15))
        details="$details\n  ❌ 核心文件缺失 (-15)"
    fi
    
    # 检查5: 近期活动 (15分)
    local has_recent_activity=false
    for logfile in "$WORKSPACE/logs/"*.log; do
        if [ -f "$logfile" ]; then
            local last_write=$(stat -c%Y "$logfile" 2>/dev/null || stat -f%m "$logfile" 2>/dev/null)
            local now=$(date +%s)
            if [ $((now - last_write)) -lt 7200 ]; then  # 2小时内
                has_recent_activity=true
                break
            fi
        fi
    done
    if [ "$has_recent_activity" = true ]; then
        ((checks_passed++))
        details="$details\n  ✅ 近期有活动记录"
    else
        score=$((score - 15))
        details="$details\n  ⚠️ 超过2小时无活动 (-15)"
    fi
    
    # 检查6: 磁盘空间 (10分)
    local disk_usage=$(df "$WORKSPACE" | tail -1 | awk '{print $5}' | tr -d '%')
    if [ "$disk_usage" -lt 80 ]; then
        ((checks_passed++))
        details="$details\n  ✅ 磁盘空间充足 (${disk_usage}%)"
    else
        score=$((score - 10))
        details="$details\n  ⚠️ 磁盘空间紧张 (${disk_usage}%) (-10)"
    fi
    
    # 保存健康评分
    cat > "$HEALTH_SCORE_FILE" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "score": $score,
    "checks_passed": $checks_passed,
    "total_checks": $total_checks,
    "threshold": $HEALTH_THRESHOLD,
    "status": "$([ $score -ge $HEALTH_THRESHOLD ] && echo 'HEALTHY' || echo 'UNHEALTHY')"
}
EOF
    
    log "📊 健康评分: $score/100 ($checks_passed/$total_checks checks passed)"
    echo -e "$details" | sed 's/^/[DETAIL] /' >> "$LOG_FILE"
    
    # 将分数写入文件供主流程读取
    echo "$score" > "$WORKSPACE/.state/last_health_score.txt"
}

# ============================================
# 3. 智能通知系统
# ============================================

send_notification() {
    local type="$1"
    local message="$2"
    local priority="${3:-normal}"
    
    log "📢 发送通知 [$priority]: $type"
    
    # 写入通知队列
    local notification_file="$WORKSPACE/.state/notifications.jsonl"
    echo "{\"time\": \"$(date -Iseconds)\", \"type\": \"$type\", \"message\": \"$message\", \"priority\": \"$priority\"}" >> "$notification_file"
    
    # 如果是高优先级，尝试多种通知方式
    if [ "$priority" = "high" ] || [ "$priority" = "critical" ]; then
        # 方式1: 系统通知（如果支持）
        if command -v notify-send &> /dev/null; then
            notify-send -u critical "死手开关警报" "$message" 2>/dev/null || true
        fi
        
        # 方式2: 写入紧急日志
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CRITICAL] $type: $message" >> "$WORKSPACE/logs/emergency.log"
        
        # 方式3: 创建标记文件（供外部监控）
        echo "$message" > "$WORKSPACE/.state/ALERT_$(date +%s).txt"
    fi
}

# ============================================
# 4. 回滚验证系统
# ============================================

verify_rollback() {
    log "🔍 验证回滚效果..."
    
    local retry_count=0
    local verification_passed=false
    
    while [ $retry_count -lt 5 ]; do
        sleep 5  # 等待服务重启
        
        local checks=0
        
        # 验证1: 进程存在
        if pgrep -f "openclaw" > /dev/null; then
            ((checks++))
        fi
        
        # 验证2: 核心文件可读
        if [ -r "$WORKSPACE/MEMORY.md" ] && [ -r "$WORKSPACE/SOUL.md" ]; then
            ((checks++))
        fi
        
        # 验证3: 内存系统可访问
        if [ -d "$WORKSPACE/memory" ] && [ $(find "$WORKSPACE/memory" -type f 2>/dev/null | wc -l) -gt 0 ]; then
            ((checks++))
        fi
        
        if [ $checks -ge 2 ]; then
            verification_passed=true
            break
        fi
        
        ((retry_count++))
        log "⏳ 回滚验证重试 $retry_count/5..."
    done
    
    if [ "$verification_passed" = true ]; then
        log "✅ 回滚验证通过"
        send_notification "ROLLBACK_SUCCESS" "回滚成功，系统已恢复正常" "high"
        return 0
    else
        log "❌ 回滚验证失败！可能需要人工干预"
        send_notification "ROLLBACK_FAILED" "回滚后验证失败，请人工检查" "critical"
        return 1
    fi
}

# ============================================
# 5. 增强回滚系统
# ============================================

rollback_to_snapshot_v2() {
    local target_snapshot="$1"
    
    log "🚨 触发回滚机制！目标: $target_snapshot"
    send_notification "ROLLBACK_STARTED" "开始回滚到 $target_snapshot" "high"
    
    # 创建当前损坏状态的备份（用于事后分析）
    local corrupted_backup="$SNAPSHOT_DIR/corrupted_$(date +%Y%m%d_%H%M%S).tar.gz"
    log "💾 保存损坏状态用于分析: $corrupted_backup"
    tar -czf "$corrupted_backup" -C "$WORKSPACE" memory MEMORY.md USER.md SOUL.md AGENTS.md IDENTITY.md config logs/*.log 2>/dev/null || true
    
    # 执行回滚
    if [ -f "$SNAPSHOT_DIR/${target_snapshot}.tar.gz" ]; then
        log "📦 正在恢复快照..."
        
        cd "$WORKSPACE"
        
        # 先解压到临时目录验证
        local temp_extract="$SNAPSHOT_DIR/.temp_rollback_$$"
        mkdir -p "$temp_extract"
        
        if ! tar -xzf "$SNAPSHOT_DIR/${target_snapshot}.tar.gz" -C "$temp_extract" 2>/dev/null; then
            log "❌ 快照解压失败！"
            rm -rf "$temp_extract"
            return 1
        fi
        
        # 验证快照完整性
        local extracted_dir=$(ls -d "$temp_extract"/snapshot_* 2>/dev/null | head -1)
        if [ ! -d "$extracted_dir" ]; then
            log "❌ 快照结构异常！"
            rm -rf "$temp_extract"
            return 1
        fi
        
        # 停止服务（如果运行中）
        if command -v openclaw &> /dev/null; then
            log "🛑 停止OpenClaw服务..."
            openclaw gateway stop 2>/dev/null || true
            sleep 2
        fi
        
        # 执行文件恢复
        log "📝 恢复核心文件..."
        for file in MEMORY.md USER.md SOUL.md AGENTS.md IDENTITY.md HEARTBEAT.md TOOLS.md; do
            if [ -f "$extracted_dir/$file" ]; then
                cp "$extracted_dir/$file" "$WORKSPACE/"
                log "  ✓ $file"
            fi
        done
        
        # 恢复memory目录
        if [ -d "$extracted_dir/memory" ]; then
            log "🧠 恢复记忆系统..."
            rm -rf "$WORKSPACE/memory"
            cp -r "$extracted_dir/memory" "$WORKSPACE/"
        fi
        
        # 恢复配置
        if [ -d "$extracted_dir/config" ]; then
            log "⚙️ 恢复配置..."
            rm -rf "$WORKSPACE/config"
            cp -r "$extracted_dir/config" "$WORKSPACE/"
        fi
        
        # 清理临时目录
        rm -rf "$temp_extract"
        
        # 重启服务
        if command -v openclaw &> /dev/null; then
            log "🔄 重启OpenClaw服务..."
            openclaw gateway start 2>/dev/null || true
            sleep 3
        fi
        
        # 验证回滚
        verify_rollback
        
        # 记录回滚事件
        cat >> "$WORKSPACE/logs/rollback-history.log" << EOF
[$(date '+%Y-%m-%d %H:%M:%S')] 回滚执行
- 触发原因: 健康评分低于阈值或心跳检测失败
- 恢复快照: $target_snapshot
- 损坏备份: $corrupted_backup
- 验证结果: $([ "$verification_passed" = true ] && echo '通过' || echo '失败')
EOF
        
        return 0
    else
        log "❌ 错误: 快照不存在: $target_snapshot"
        return 1
    fi
}

# ============================================
# 6. 主流程
# ============================================

main() {
    log "═══════════════════════════════════════"
    log "🛡️ 死手开关 v2.0 检测开始"
    log "═══════════════════════════════════════"
    
    # 步骤1: 创建增量快照
    local current_snapshot=$(save_incremental_snapshot)
    
    # 步骤2: 深度健康检测
calculate_health_score
local health_score=$(cat "$WORKSPACE/.state/last_health_score.txt" 2>/dev/null || echo "0")
    
    # 步骤3: 确定回滚目标（3小时前的快照）
    local target_rollback=""
    local cutoff_time=$(($(date +%s) - 10800))
    
    # 读取manifest找到合适的回滚目标
    if [ -f "$SNAPSHOT_DIR/manifest.json" ]; then
        target_rollback=$(jq -r '.snapshots[] | select(.timestamp | fromdateiso8601 | . <= '"$cutoff_time"') | .id' "$SNAPSHOT_DIR/manifest.json" 2>/dev/null | tail -1)
    fi
    
    # 备用方案：按文件名查找
    if [ -z "$target_rollback" ]; then
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
    fi
    
    if [ -z "$target_rollback" ]; then
        log "⚠️ 未找到3小时前的快照，将使用最早的可用快照"
        target_rollback=$(ls -t "$SNAPSHOT_DIR"/snapshot_*.tar.gz 2>/dev/null | tail -1 | xargs basename 2>/dev/null | sed 's/.tar.gz//')
    fi
    
    if [ -n "$target_rollback" ]; then
        log "🎯 回滚目标: $target_rollback"
    else
        log "⚠️ 警告: 没有可用的回滚目标"
    fi
    
    # 步骤4: 决策
    if [ "$health_score" -ge "$HEALTH_THRESHOLD" ]; then
        log "✅ 健康检测通过 (评分: $health_score/${HEALTH_THRESHOLD})"
        log "💾 当前快照: $current_snapshot"
        send_notification "HEALTH_CHECK_PASSED" "健康评分: $health_score/100" "normal"
    else
        log "🚨 健康评分过低: $health_score/${HEALTH_THRESHOLD}"
        send_notification "HEALTH_CHECK_FAILED" "健康评分过低: $health_score，准备回滚" "high"
        
        if [ -n "$target_rollback" ]; then
            rollback_to_snapshot_v2 "$target_rollback"
        else
            log "❌ 无法回滚：没有可用的快照"
            send_notification "ROLLBACK_IMPOSSIBLE" "健康异常但无快照可回滚" "critical"
        fi
    fi
    
    log "═══════════════════════════════════════"
    log "检测结束"
    log "═══════════════════════════════════════"
}

# 执行
main "$@"
