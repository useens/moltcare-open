#!/bin/bash
# mode-controller.sh - 森森模式切换控制器
# 用法: ./mode-controller.sh [performance|balanced|eco|frozen|status]

MODE_FILE="/root/.openclaw/workspace/memory/current-mode.json"
MODE_CONFIG="/root/.openclaw/workspace/config/mode-management.md"

# 默认模式
DEFAULT_MODE="balanced"

# 模式配置
get_mode_config() {
    case $1 in
        performance)
            echo '{"name":"性能模式","thinking":"high","max_tokens":8192,"parallel":5,"cost":"~1500t/min"}'
            ;;
        balanced)
            echo '{"name":"均衡模式","thinking":"low","max_tokens":4096,"parallel":2,"cost":"~200t/min"}'
            ;;
        eco)
            echo '{"name":"节能模式","thinking":"off","max_tokens":1024,"parallel":1,"cost":"~50t/min"}'
            ;;
        frozen)
            echo '{"name":"冻结模式","thinking":"none","max_tokens":0,"parallel":0,"cost":"0t/min"}'
            ;;
        *)
            echo "{}"
            ;;
    esac
}

# 切换模式
switch_mode() {
    local new_mode=$1
    local timestamp=$(date -Iseconds)
    
    # 保存历史
    if [ -f "$MODE_FILE" ]; then
        local old_mode=$(cat "$MODE_FILE" | grep -o '"mode":"[^"]*"' | cut -d'"' -f4)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $old_mode -> $new_mode" >> /root/.openclaw/workspace/memory/mode-history.log
    fi
    
    # 写入新配置
    cat > "$MODE_FILE" <<EOF
{
    "mode": "$new_mode",
    "config": $(get_mode_config $new_mode),
    "switched_at": "$timestamp",
    "reason": "manual"
}
EOF
    
    echo "✅ 已切换至: $(get_mode_config $new_mode | grep -o '"name":"[^"]*"' | cut -d'"' -f4)"
}

# 显示状态
show_status() {
    if [ -f "$MODE_FILE" ]; then
        cat "$MODE_FILE"
    else
        echo "当前无模式配置，默认: 均衡模式"
    fi
}

# 主逻辑
case ${1:-status} in
    performance|p)
        switch_mode "performance"
        ;;
    balanced|b)
        switch_mode "balanced"
        ;;
    eco|e)
        switch_mode "eco"
        ;;
    frozen|f)
        switch_mode "frozen"
        ;;
    status|s|*)
        show_status
        ;;
esac