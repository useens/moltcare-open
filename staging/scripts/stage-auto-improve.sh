#!/bin/bash
# stage-auto-improve.sh - 自动自我改进系统
# 触发条件: 信号检测 | 时间间隔 | 学习债务积压

set -e

WORKSPACE="/root/.openclaw/workspace"
STAGING="$WORKSPACE/staging"
LOG_FILE="$STAGING/logs/auto-improve.log"
SIGNAL_FILE="$STAGING/logs/improve-signal.json"

mkdir -p "$STAGING/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_improve_signal() {
    # 检查自我改进信号
    # 返回: strong|medium|weak|none
    
    local signal_strength="none"
    local reasons=()
    
    # 信号1: 学习债务积压 > 5条
    if [[ -f "$WORKSPACE/memory/learning-debt.md" ]]; then
        local debt_count=$(grep -c "^\-" "$WORKSPACE/memory/learning-debt.md" 2>/dev/null || echo "0")
        if [[ $debt_count -gt 5 ]]; then
            reasons+=("学习债务积压: $debt_count条")
            signal_strength="medium"
        fi
        if [[ $debt_count -gt 10 ]]; then
            signal_strength="strong"
        fi
    fi
    
    # 信号2: 上次改进时间 > 24小时
    if [[ -f "$SIGNAL_FILE" ]]; then
        local last_improve=$(jq -r '.last_improve' "$SIGNAL_FILE" 2>/dev/null || echo "0")
        local current_time=$(date +%s)
        local hours_since=$(( (current_time - last_improve) / 3600 ))
        if [[ $hours_since -gt 24 ]]; then
            reasons+=("距上次改进已过 $hours_since 小时")
            [[ "$signal_strength" == "none" ]] && signal_strength="weak"
        fi
        if [[ $hours_since -gt 48 ]]; then
            signal_strength="medium"
        fi
        if [[ $hours_since -gt 72 ]]; then
            signal_strength="strong"
        fi
    fi
    
    # 信号3: 待处理任务 > 3个 (检测memory/)
    local pending_tasks=$(find "$WORKSPACE/memory" -name "*.pending" 2>/dev/null | wc -l)
    if [[ $pending_tasks -gt 3 ]]; then
        reasons+=("待处理任务: $pending_tasks个")
        [[ "$signal_strength" != "strong" ]] && signal_strength="medium"
    fi
    
    # 输出结果
    local result='{"strength":"'$signal_strength'","reasons":['
    local first=true
    for reason in "${reasons[@]}"; do
        [[ "$first" == "false" ]] && result+=","
        result+='"'$reason'"'
        first=false
    done
    result+=']}'
    
    echo "$result"
}

select_improve_target() {
    # 根据信号选择改进目标
    local target=""
    local reason=""
    
    # 优先级判断
    if [[ -f "$WORKSPACE/memory/learning-debt.md" ]]; then
        # 检查是否有高Signal内容
        local high_signal=$(grep -E "Signal\s*(9|10)" "$WORKSPACE/memory/learning-debt.md" | wc -l)
        if [[ $high_signal -gt 0 ]]; then
            echo '{"file":"AGENTS.md","reason":"学习债务中有高Signal内容，需要更新操作手册"}'
            return
        fi
    fi
    
    # 检查SOUL.md是否需要更新
    if [[ ! -f "$STAGING/SOUL.md" ]]; then
        echo '{"file":"SOUL.md","reason":"核心原则文件尚未进入staging系统"}'
        return
    fi
    
    # 默认轮换
    local files=("AGENTS.md" "SOUL.md" "MEMORY.md" "USER.md")
    local index=$(( $(date +%s) % 4 ))
    local selected="${files[$index]}"
    echo '{"file":"'$selected'","reason":"定期轮换优化"}'
}

generate_improve_prompt() {
    local target_file="$1"
    local reason="$2"
    
    cat << EOF
基于当前系统状态和目标，请在 staging/$target_file 中进行一次自我改进。

改进目标: $reason

改进方向建议 (选择1-2个):
1. 完善缺失的使用说明或文档
2. 添加常见错误和解决方案
3. 优化工作流程或检查清单
4. 补充新的能力描述或使用场景
5. 修正过时或不准确的内容

要求:
- 改动应有实际价值，不要形式化修改
- 保持现有格式和风格一致
- 添加的内容应该经过深思熟虑
- 遵循MD文档的最佳实践

请在 staging/$target_file 中实现改进，然后使用 stage-validate.sh 验证，最后用 stage-deploy.sh 部署。
EOF
}

main() {
    log "=== 自动自我改进检查启动 ==="
    
    # 检查是否需要运行
    if [[ -f "$WORKSPACE/.improve-lock" ]]; then
        log "已有改进进程在执行，跳过"
        exit 0
    fi
    
    # 检测信号
    log "检测改进信号..."
    local signal_info=$(check_improve_signal)
    local strength=$(echo "$signal_info" | jq -r '.strength')
    
    log "信号强度: $strength"
    
    if [[ "$strength" == "none" ]]; then
        log "无改进信号，退出"
        exit 0
    fi
    
    if [[ "$strength" == "weak" ]]; then
        # 弱信号: 简单检查即可
        log "弱信号，仅记录，不执行"
        exit 0
    fi
    
    # 创建锁文件
    touch "$WORKSPACE/.improve-lock"
    
    log "触发自动改进 (强度: $strength)"
    
    # 选择目标
    local target_info=$(select_improve_target)
    local target_file=$(echo "$target_info" | jq -r '.file')
    local reason=$(echo "$target_info" | jq -r '.reason')
    
    log "改进目标: $target_file"
    log "原因: $reason"
    
    # 确保目标文件在staging中
    if [[ ! -f "$STAGING/$target_file" ]]; then
        cp "$WORKSPACE/$target_file" "$STAGING/$target_file"
        log "复制 $target_file 到 staging"
    fi
    
    # 生成改进提示（输出到日志，供以后参考）
    local improve_prompt=$(generate_improve_target "$target_file" "$reason")
    log "改进提示已生成"
    
    # 更新信号文件
    echo '{"last_improve":'$(date +%s)',"strength":"'$strength'","target":"'$target_file'"}' > "$SIGNAL_FILE"
    
    # 移除锁文件
    rm -f "$WORKSPACE/.improve-lock"
    
    log "=== 检查完成，等待下次触发 ==="
    
    # 输出摘要 (可用于通知)
    echo '{"action":"ready","strength":"'$strength'","target":"'$target_file'","reason":"'$reason'"}'
}

# 执行
main
