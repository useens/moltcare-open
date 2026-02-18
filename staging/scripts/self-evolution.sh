#!/bin/bash
# self-evolution.sh - 自我进化引擎
# 完整流程: 检测 → 切换k2p5 → 改进 → 验证 → 部署 → 恢复模型

set -e

WORKSPACE="/root/.openclaw/workspace"
STAGING="$WORKSPACE/staging"
SCRIPTS="$STAGING/scripts"
LOG="$STAGING/logs/evolution.log"
EVOLUTION_MARKER="$WORKSPACE/.evolution-active"

mkdir -p "$STAGING/logs"

log() {
    echo "[$(date '+%H:%M:%S')] $1" >> "$LOG"
}

# ============ 阶段1: 检测 ============
detect_signal() {
    log "🔍 检测改进信号..."
    
    local score=0
    local reasons=""
    
    # 信号1: 学习债务数量
    if [[ -f "$WORKSPACE/memory/learning-debt.md" ]]; then
        local debt=$(grep -c "^- " "$WORKSPACE/memory/learning-debt.md" 2>/dev/null || echo "0")
        if [[ $debt -gt 10 ]]; then score=$((score+3)); reasons+="债务积压($debt) "; fi
        if [[ $debt -gt 5 ]]; then score=$((score+2)); reasons+="债务增长 "; fi
    fi
    
    # 信号2: 距上次进化时间
    if [[ -f "$STAGING/logs/last-evolution" ]]; then
        local last=$(cat "$STAGING/logs/last-evolution")
        local now=$(date +%s)
        local hours=$(( (now - last) / 3600 ))
        if [[ $hours -gt 48 ]]; then score=$((score+3)); reasons+="超过48小时 "; fi
        if [[ $hours -gt 24 ]]; then score=$((score+1)); fi
    else
        score=$((score+2)); reasons+="首次进化 "
    fi
    
    # 信号3: 系统健康检查异常
    if [[ -f "$WORKSPACE/scripts/unified-monitor.py" ]]; then
        if ! python3 "$WORKSPACE/scripts/unified-monitor.py" --check-only 2>/dev/null; then
            score=$((score+2)); reasons+="健康检查异常 "
        fi
    fi
    
    log "信号评分: $score/9 ($reasons)"
    
    if [[ $score -ge 5 ]]; then
        echo "strong"
    elif [[ $score -ge 3 ]]; then
        echo "medium"
    else
        echo "weak"
    fi
}

# ============ 阶段2: 选择目标 ============
select_target() {
    log "🎯 选择改进目标..."
    
    # 优先级队列
    local candidates=("AGENTS.md" "SOUL.md" "MEMORY.md" "USER.md" "IDENTITY.md" "TOOLS.md")
    
    # 基于内容的智能选择
    for file in "${candidates[@]}"; do
        if [[ -f "$STAGING/$file" ]]; then
            # 检查文件年龄(如果很久没更新)
            local age=$(( ($(date +%s) - $(stat -c %Y "$STAGING/$file" 2>/dev/null || echo "0") ) / 3600 ))
            if [[ $age -gt 48 ]]; then
                echo "$file"
                log "选择: $file (已${age}小时未更新)"
                return
            fi
        fi
    done
    
    # 默认: 轮换
    local idx=$(( $(date +%s) % ${#candidates[@]} ))
    echo "${candidates[$idx]}"
    log "选择: ${candidates[$idx]} (轮换)"
}

# ============ 阶段3: 执行改进 (核心) ============
execute_improvement() {
    local target="$1"
    log "🔧 开始改进: $target"
    
    # 创建进化标记(防止重复触发)
    echo "$(date +%s)" > "$EVOLUTION_MARKER"
    echo "$target" >> "$EVOLUTION_MARKER"
    
    # 生成改进策略
    local strategy=$(generate_strategy "$target")
    log "策略: $strategy"
    
    # 记录: 这里会通知Agent进入k2p5模式并执行改进
    # 实际执行由上层调用者完成
    echo "$strategy"
}

generate_strategy() {
    local file="$1"
    local strategies=(
        "添加实用章节: 常见错误清单"
        "优化工作流程: 简化步骤"
        "补充缺失内容: 使用示例"
        "改进可读性: 表格和结构化"
        "添加检查点: 验证清单"
        "更新时间戳: 版本信息"
    )
    
    # 基于文件类型选择策略
    case "$file" in
        "AGENTS.md")
            echo "${strategies[0]}|${strategies[2]}"
            ;;
        "SOUL.md")
            echo "${strategies[1]}|${strategies[4]}"
            ;;
        "MEMORY.md")
            echo "${strategies[3]}|${strategies[5]}"
            ;;
        *)
            echo "${strategies[$((RANDOM % 6))]}"
            ;;
    esac
}

# ============ 阶段4: 验证和部署 ============
verify_and_deploy() {
    local target="$1"
    log "✅ 验证并部署: $target"
    
    # 验证
    if ! "$SCRIPTS/stage-validate.sh" "$target"; then
        log "❌ 验证失败，放弃部署"
        return 1
    fi
    
    # 部署
    if "$SCRIPTS/stage-deploy.sh" "$target"; then
        log "✅ 部署成功"
        # 记录进化时间
        date +%s > "$STAGING/logs/last-evolution"
        return 0
    else
        log "❌ 部署失败"
        return 1
    fi
}

# ============ 阶段5: 清理 ============
cleanup() {
    log "🧹 清理进化标记"
    rm -f "$EVOLUTION_MARKER"
}

# ============ 主流程 ============
main() {
    log ""
    log "🌲 自我进化引擎启动"
    log "=========================="
    
    # 检查是否已在进化中
    if [[ -f "$EVOLUTION_MARKER" ]]; then
        local start_time=$(head -1 "$EVOLUTION_MARKER")
        local elapsed=$(( $(date +%s) - start_time ))
        if [[ $elapsed -lt 3600 ]]; then
            log "进化已在进行中(${elapsed}s前启动)，跳过"
            exit 0
        fi
        # 超过1小时，清理旧标记
        rm -f "$EVOLUTION_MARKER"
    fi
    
    # 阶段1: 检测
    local signal=$(detect_signal)
    
    if [[ "$signal" == "weak" ]]; then
        log "信号不足(weak)，本次跳过"
        exit 0
    fi
    
    log "🚀 信号充足($signal)，启动进化流程"
    
    # 阶段2: 选择目标
    local target=$(select_target)
    
    # 确保文件在staging中
    if [[ ! -f "$STAGING/$target" ]]; then
        cp "$WORKSPACE/$target" "$STAGING/$target"
        log "复制 $target 到 staging"
    fi
    
    # 阶段3: 执行(输出策略供上层使用)
    local strategy=$(execute_improvement "$target")
    
    # 输出结果(JSON格式，供Cron解析)
    cat << EOF
{
    "status": "ready",
    "signal": "$signal", 
    "target": "$target",
    "strategy": "$strategy",
    "model": "k2p5",
    "workspace": "$WORKSPACE"
}
EOF
    
    log "✅ 进化准备完成，等待执行"
}

main
