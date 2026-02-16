#!/bin/bash
# k2p5智能难度评估脚本
# 根据用户输入自动判断thinking模式

analyze_difficulty() {
    local input="$1"
    local score=1  # 默认L1简单
    
    # L4极难关键词检测
    if echo "$input" | grep -qiE "(从零设计|核心架构|大规模|高可用|容灾|疑难|诡异bug|深度优化|系统重构)"; then
        score=4
    # L3困难关键词检测
    elif echo "$input" | grep -qiE "(架构|设计|策略|复杂算法|分布式|并发|性能|微服务|多系统|集成)"; then
        score=3
    # L2中等关键词检测
    elif echo "$input" | grep -qiE "(函数|模块|实现|接口|调试|测试|优化|重构|设计模式)"; then
        score=2
    # L1简单关键词检测
    elif echo "$input" | grep -qiE "(语法|报错|怎么写|示例|修复|简单)"; then
        score=1
    fi
    
    # 长度权重
    local length=${#input}
    if [ $length -gt 1000 ]; then
        score=$((score + 2))
    elif [ $length -gt 500 ]; then
        score=$((score + 1))
    fi
    
    # 上下文权重
    if echo "$input" | grep -qiE "(生产环境|紧急|线上问题|架构评审)"; then
        score=$((score + 1))
    fi
    
    # 降级规则
    if echo "$input" | grep -qiE "(简单问题|快速看一下|小问题)"; then
        score=$((score - 1))
    fi
    
    # 限制范围 1-4
    if [ $score -lt 1 ]; then score=1; fi
    if [ $score -gt 4 ]; then score=4; fi
    
    echo "$score"
}

# 根据分数返回thinking模式
get_thinking_mode() {
    local score=$1
    case $score in
        1) echo "off" ;;
        2) echo "concise" ;;
        3) echo "on" ;;
        4) echo "stream" ;;
        *) echo "off" ;;
    esac
}

# 主函数
main() {
    local user_input="$1"
    local score=$(analyze_difficulty "$user_input")
    local mode=$(get_thinking_mode $score)
    
    echo "{"
    echo "  \"input_length\": ${#user_input},"
    echo "  \"difficulty_score\": $score,"
    echo "  \"thinking_mode\": \"$mode\","
    echo "  \"level\": \"L$score\""
    echo "}"
}

# 如果直接运行，测试示例
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    if [ -z "$1" ]; then
        # 测试用例
        echo "测试用例:"
        echo ""
        echo "1. 简单问题:"
        echo "输入: 这段代码报错了怎么修复"
        main "这段代码报错了怎么修复"
        echo ""
        echo "2. 中等问题:"
        echo "输入: 帮我设计一个用户认证的模块"
        main "帮我设计一个用户认证的模块"
        echo ""
        echo "3. 困难问题:"
        echo "输入: 设计一个高可用的微服务架构，支持10万并发"
        main "设计一个高可用的微服务架构，支持10万并发"
    else
        main "$1"
    fi
fi
