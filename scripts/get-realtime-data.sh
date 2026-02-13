#!/bin/bash
# 实时数据获取脚本 - 强制使用真实数据
# 禁止从缓存读取

WORKSPACE="/root/.openclaw/workspace"

# 获取真实超进化周期数
get_real_cycles() {
    if [ -f "$WORKSPACE/memory/hyper-evolution-state.json" ]; then
        START_TIME=$(cat "$WORKSPACE/memory/hyper-evolution-state.json" | grep -o '"start_time": "[^"]*"' | cut -d'"' -f4)
        if [ -n "$START_TIME" ]; then
            START_EPOCH=$(date -d "$START_TIME" +%s 2>/dev/null || echo "0")
            CURRENT_EPOCH=$(date +%s)
            ELAPSED_HOURS=$(( (CURRENT_EPOCH - START_EPOCH) / 3600 ))
            REAL_CYCLES=$(( ELAPSED_HOURS * 6 ))  # 每10分钟一个周期
            echo "$REAL_CYCLES"
            return 0
        fi
    fi
    echo "unknown"
    return 1
}

# 获取真实运行时长
get_real_duration() {
    if [ -f "$WORKSPACE/memory/hyper-evolution-state.json" ]; then
        START_TIME=$(cat "$WORKSPACE/memory/hyper-evolution-state.json" | grep -o '"start_time": "[^"]*"' | cut -d'"' -f4)
        if [ -n "$START_TIME" ]; then
            START_EPOCH=$(date -d "$START_TIME" +%s 2>/dev/null || echo "0")
            CURRENT_EPOCH=$(date +%s)
            ELAPSED_HOURS=$(( (CURRENT_EPOCH - START_EPOCH) / 3600 ))
            echo "${ELAPSED_HOURS}小时"
            return 0
        fi
    fi
    echo "unknown"
    return 1
}

# 主函数
case "$1" in
    cycles)
        get_real_cycles
        ;;
    duration)
        get_real_duration
        ;;
    *)
        echo "用法: $0 [cycles|duration]"
        exit 1
        ;;
esac
