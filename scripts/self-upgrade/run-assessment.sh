#!/bin/bash
# -*- coding: utf-8 -*-
# Sensen Intelligence Assessment Runner
# 智能水平评估执行脚本
#
# 用法: ./run-assessment.sh [mode]
# mode: high | medium | emergency

set -e

# 配置
WORKSPACE_DIR="/root/.openclaw/workspace"
SCRIPT_DIR="$WORKSPACE_DIR/scripts/self-upgrade"
MEMORY_DIR="$WORKSPACE_DIR/memory/self-upgrade"
LOG_DIR="/var/log/sensen-upgrade"

# 确保目录存在
mkdir -p "$MEMORY_DIR" "$LOG_DIR"

# 参数
MODE="${1:-medium}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE_STR=$(date '+%Y%m%d_%H%M%S')

# 日志函数
log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_DIR/assessment.log"
}

# 报告文件
REPORT_FILE="$MEMORY_DIR/assessment_report_${DATE_STR}.json"

log "========================================"
log "🧠 启动智能水平评估 - 模式: $MODE"
log "========================================"

# Python 辅助计算函数
py_calc() {
    python3 -c "print($1)"
}

# 限制值范围
clamp() {
    local val=$1
    if (( $(echo "$val > 1.0" | python3 -c "import sys; print(1 if float(sys.stdin.read().split()[0]) > 1.0 else 0)") )); then
        echo "1.0"
    elif (( $(echo "$val < 0.1" | python3 -c "import sys; print(1 if float(sys.stdin.read().split()[0]) < 0.1 else 0)") )); then
        echo "0.1"
    else
        echo "$val"
    fi
}

# 初始化结果
declare -A RESULTS

# 评估维度 1: 代码质量
evaluate_code_quality() {
    log "📊 评估: 代码质量"
    
    local score=0.75
    local issues=0
    
    # 检查脚本数量
    local script_count=$(find "$WORKSPACE_DIR/scripts" -type f \( -name "*.py" -o -name "*.sh" \) 2>/dev/null | wc -l)
    if [ "$script_count" -gt 50 ]; then
        score=$(py_calc "$score + 0.05")
    fi
    
    # 检查是否有语法错误
    local python_errors=0
    while IFS= read -r file; do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            ((python_errors++))
        fi
    done < <(find "$WORKSPACE_DIR/scripts" -name "*.py" -type f 2>/dev/null)
    
    if [ "$python_errors" -eq 0 ]; then
        score=$(py_calc "$score + 0.05")
    else
        score=$(py_calc "$score - 0.05")
        issues=$((issues + python_errors))
    fi
    
    # 检查bash脚本语法
    local bash_errors=0
    while IFS= read -r file; do
        if ! bash -n "$file" 2>/dev/null; then
            ((bash_errors++))
        fi
    done < <(find "$WORKSPACE_DIR/scripts" -name "*.sh" -type f 2>/dev/null)
    
    if [ "$bash_errors" -eq 0 ]; then
        score=$(py_calc "$score + 0.05")
    else
        score=$(py_calc "$score - 0.03")
    fi
    
    # 限制最大值
    score=$(python3 -c "print(min(1.0, max(0.1, $score)))")
    
    RESULTS["code_quality"]=$score
    log "  代码质量得分: $score (问题数: $issues)"
}

# 评估维度 2: 执行效率
evaluate_execution_efficiency() {
    log "📊 评估: 执行效率"
    
    local score=0.70
    
    # 检查系统负载
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    local cpu_cores=$(nproc)
    
    # 使用Python进行比较
    if python3 -c "import sys; exit(0 if float('$load_avg') < $cpu_cores else 1)"; then
        score=$(py_calc "$score + 0.10")
    elif python3 -c "import sys; exit(0 if float('$load_avg') > $cpu_cores * 2 else 1)"; then
        score=$(py_calc "$score - 0.10")
    fi
    
    # 检查内存使用
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$mem_usage" -lt 70 ]; then
        score=$(py_calc "$score + 0.05")
    elif [ "$mem_usage" -gt 90 ]; then
        score=$(py_calc "$score - 0.10")
    fi
    
    # 限制范围
    score=$(python3 -c "print(min(1.0, max(0.1, $score)))")
    
    RESULTS["execution_efficiency"]=$score
    log "  执行效率得分: $score (负载: $load_avg, 内存: ${mem_usage}%)"
}

# 评估维度 3: 错误恢复能力
evaluate_error_recovery() {
    log "📊 评估: 错误恢复能力"
    
    local score=0.65
    
    # 检查最近的错误日志
    local recent_errors=0
    if [ -d "$LOG_DIR" ]; then
        recent_errors=$(find "$LOG_DIR" -name "*.log" -mtime -1 -exec grep -i "error\|exception\|failed" {} + 2>/dev/null | wc -l)
    fi
    
    if [ "$recent_errors" -eq 0 ]; then
        score=$(py_calc "$score + 0.15")
    elif [ "$recent_errors" -lt 10 ]; then
        score=$(py_calc "$score + 0.05")
    elif [ "$recent_errors" -gt 50 ]; then
        score=$(py_calc "$score - 0.15")
    fi
    
    # 检查自动恢复脚本存在性
    if [ -f "$SCRIPT_DIR/../auto_fix_system.py" ]; then
        score=$(py_calc "$score + 0.05")
    fi
    
    # 限制范围
    score=$(python3 -c "print(min(1.0, max(0.1, $score)))")
    
    RESULTS["error_recovery"]=$score
    log "  错误恢复得分: $score (近期错误: $recent_errors)"
}

# 评估维度 4: 学习速度
evaluate_learning_speed() {
    log "📊 评估: 学习速度"
    
    local score=0.60
    
    # 检查最近新增的技能/脚本
    local recent_scripts=$(find "$WORKSPACE_DIR/scripts" -type f -mtime -7 \( -name "*.py" -o -name "*.sh" \) 2>/dev/null | wc -l)
    
    if [ "$recent_scripts" -gt 10 ]; then
        score=$(py_calc "$score + 0.20")
    elif [ "$recent_scripts" -gt 5 ]; then
        score=$(py_calc "$score + 0.10")
    elif [ "$recent_scripts" -gt 0 ]; then
        score=$(py_calc "$score + 0.05")
    fi
    
    # 检查文档更新
    local recent_docs=$(find "$WORKSPACE_DIR" -maxdepth 1 -name "*.md" -mtime -7 2>/dev/null | wc -l)
    if [ "$recent_docs" -gt 0 ]; then
        score=$(py_calc "$score + 0.05")
    fi
    
    # 限制范围
    score=$(python3 -c "print(min(1.0, $score))")
    
    RESULTS["learning_speed"]=$score
    log "  学习速度得分: $score (7天内新增: $recent_scripts)"
}

# 评估维度 5: 自主性
evaluate_autonomy() {
    log "📊 评估: 自主性"
    
    local score=0.80
    
    # 检查自动化脚本数量
    local auto_scripts=$(find "$WORKSPACE_DIR/scripts" -type f \( -name "*auto*" -o -name "*daemon*" -o -name "*schedule*" \) 2>/dev/null | wc -l)
    
    if [ "$auto_scripts" -gt 10 ]; then
        score=$(py_calc "$score + 0.10")
    elif [ "$auto_scripts" -gt 5 ]; then
        score=$(py_calc "$score + 0.05")
    fi
    
    # 检查systemd服务
    if systemctl list-unit-files 2>/dev/null | grep -q "sensen"; then
        score=$(py_calc "$score + 0.05")
    fi
    
    # 限制范围
    score=$(python3 -c "print(min(1.0, $score))")
    
    RESULTS["autonomy"]=$score
    log "  自主性得分: $score (自动化脚本: $auto_scripts)"
}

# 评估维度 6: 验证能力
evaluate_verification() {
    log "📊 评估: 验证能力"
    
    local score=0.70
    
    # 检查验证脚本存在性
    if [ -f "$WORKSPACE_DIR/scripts/upgrade-verifier.py" ]; then
        score=$(py_calc "$score + 0.10")
    fi
    
    if [ -f "$SCRIPT_DIR/verify-upgrade.py" ]; then
        score=$(py_calc "$score + 0.10")
    fi
    
    # 检查验证历史
    if [ -d "$MEMORY_DIR" ]; then
        local verify_history=$(find "$MEMORY_DIR" -name "*verify*" -type f 2>/dev/null | wc -l)
        if [ "$verify_history" -gt 0 ]; then
            score=$(py_calc "$score + 0.05")
        fi
    fi
    
    # 限制范围
    score=$(python3 -c "print(min(1.0, $score))")
    
    RESULTS["verification"]=$score
    log "  验证能力得分: $score"
}

# 深度评估额外检查
run_deep_checks() {
    log "🔍 执行深度评估额外检查..."
    
    # 执行系统优化机会扫描
    if [ -f "$WORKSPACE_DIR/scripts/optimization-opportunity-finder.py" ]; then
        log "  运行优化机会扫描..."
        timeout 120 python3 "$WORKSPACE_DIR/scripts/optimization-opportunity-finder.py" 2>/dev/null || true
    fi
    
    # 执行弱点分析
    if [ -f "$WORKSPACE_DIR/scripts/weakness-analyzer.py" ]; then
        log "  运行弱点分析..."
        timeout 120 python3 "$WORKSPACE_DIR/scripts/weakness-analyzer.py" 2>/dev/null || true
    fi
    
    log "✅ 深度评估额外检查完成"
}

# 生成报告
generate_report() {
    log "📝 生成评估报告..."
    
    # 计算综合得分 (使用Python)
    local overall=$(python3 -c "
scores = [${RESULTS["code_quality"]}, ${RESULTS["execution_efficiency"]}, ${RESULTS["error_recovery"]}, ${RESULTS["learning_speed"]}, ${RESULTS["autonomy"]}, ${RESULTS["verification"]}]
print(round(sum(scores) / len(scores), 2))
")
    
    # 构建JSON报告
    cat > "$REPORT_FILE" << EOF
{
  "timestamp": "$TIMESTAMP",
  "mode": "$MODE",
  "overall_score": $overall,
  "dimensions": {
    "code_quality": ${RESULTS["code_quality"]},
    "execution_efficiency": ${RESULTS["execution_efficiency"]},
    "error_recovery": ${RESULTS["error_recovery"]},
    "learning_speed": ${RESULTS["learning_speed"]},
    "autonomy": ${RESULTS["autonomy"]},
    "verification": ${RESULTS["verification"]}
  },
  "hostname": "$(hostname)",
  "assessment_version": "1.0.0"
}
EOF
    
    log "📄 报告已保存: $REPORT_FILE"
    log "📊 综合得分: $overall"
}

# 主执行流程
main() {
    log "开始执行$MODE级别评估..."
    
    # 执行各维度评估
    evaluate_code_quality
    evaluate_execution_efficiency
    evaluate_error_recovery
    evaluate_learning_speed
    evaluate_autonomy
    evaluate_verification
    
    # 深度模式额外检查
    if [ "$MODE" = "high" ]; then
        run_deep_checks
    fi
    
    # 生成报告
    generate_report
    
    log "========================================"
    log "✅ 评估完成 - 模式: $MODE"
    log "========================================"
    
    # 输出JSON结果给调用者
    cat "$REPORT_FILE"
}

# 执行主函数
main
