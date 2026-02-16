#!/bin/bash
# 统一智能路由系统 - 所有模型
# 根据任务类型和复杂度自动选择模型和thinking模式

USER_INPUT="$1"
CURRENT_MODEL="${2:-ds}"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🤖 智能路由分析${NC}"
echo "=================="
echo "输入: $USER_INPUT"
echo "当前模型: $CURRENT_MODEL"
echo ""

# 辅助函数：判断难度级别（L1-L5）
judge_difficulty() {
    local input="$1"
    local level=2  # 默认L2

    # L5极难关键词
    if echo "$input" | grep -qiE "(从零设计|核心架构|大规模|高可用|容灾|疑难|诡异bug|深度优化|系统重构|极限|瓶颈)"; then
        level=5
    # L4困难关键词
    elif echo "$input" | grep -qiE "(架构|设计|策略|复杂算法|分布式|并发|性能|微服务|多系统|集成|数据流)"; then
        level=4
    # L3中等关键词
    elif echo "$input" | grep -qiE "(函数|模块|实现|接口|调试|测试|优化|重构|设计模式|API)"; then
        level=3
    # L2简单关键词
    elif echo "$input" | grep -qiE "(语法|报错|怎么写|示例|修复|简单|配置|基本概念)"; then
        level=2
    # L1极简关键词
    elif echo "$input" | grep -qiE "(你好|在吗|状态|当前|几点|今天|确认|好的|取消|是|否)"; then
        level=1
    fi

    # 长度权重
    local length=${#input}
    if [ $length -gt 1000 ]; then
        level=$((level + 1))
    elif [ $length -gt 500 ]; then
        level=$((level + 0.5))
    fi

    # 上下文权重
    if echo "$input" | grep -qiE "(生产环境|紧急|线上问题|架构评审)"; then
        level=$((level + 1))
    fi

    # 降级权重
    if echo "$input" | grep -qiE "(快速看一下|小问题|极简)"; then
        level=$((level - 1.5))
    elif echo "$input" | grep -qiE "(简单问题)"; then
        level=$((level - 1))
    fi

    # 限制范围 1-5
    if [ $level -lt 1 ]; then level=1; fi
    if [ $level -gt 5 ]; then level=5; fi

    echo "$level"
}

# 辅助函数：根据难度和模型获取thinking模式
get_thinking_mode() {
    local difficulty=$1
    local model=$2
    local level_int=$(echo "$difficulty" | cut -d. -f1)

    case $level_int in
        1)
            echo "off"
            ;;
        2)
            if [ "$model" = "ds" ]; then
                echo "off"
            else
                echo "concise"
            fi
            ;;
        3)
            if [ "$model" = "ds" ] || [ "$model" = "kimi" ]; then
                echo "concise"
            else
                echo "on"
            fi
            ;;
        4)
            echo "on"
            ;;
        5)
            if [ "$model" = "k2p5" ]; then
                echo "stream"
            else
                echo "on"
            fi
            ;;
        *)
            echo "off"
            ;;
    esac
}

# 主流程
DIFFICULTY=$(judge_difficulty "$USER_INPUT")

# 模型选择逻辑
SUGGESTED_MODEL=""
REASON=""

# 检查图片/长文档
if echo "$USER_INPUT" | grep -qiE "(图片|截图|文档|pdf|长文|整本书|分析图表)"; then
    SUGGESTED_MODEL="kimi"
    REASON="检测到图片或长文档，256k上下文"
# 检测代码任务
elif echo "$USER_INPUT" | grep -qiE "(代码|Python|Java|JavaScript|Go|Rust|bug|调试|算法|架构)"; then
    if [ "$DIFFICULTY" -ge 4 ]; then
        SUGGESTED_MODEL="k2p5"
        REASON="复杂代码任务，需要最强能力"
    else
        SUGGESTED_MODEL="glm"
        REASON="普通代码任务，glm快速响应"
    fi
# 检测中文优化
elif echo "$USER_INPUT" | grep -qiE "(中文|翻译|文案|本地化)"; then
    SUGGESTED_MODEL="glm"
    REASON="中文处理优化"
# 默认
else
    SUGGESTED_MODEL="ds"
    REASON="通用任务，ds推理能力强"
fi

# 计算thinking模式
THINKING_MODE=$(get_thinking_mode "$DIFFICULTY" "$SUGGESTED_MODEL")

# 显示建议
echo -e "${YELLOW}💡 建议切换${NC}"
echo "=================="
echo "当前: $CURRENT_MODEL"
echo "建议: $SUGGESTED_MODEL"
echo "难度级别: L${DIFFICULTY}"
echo "Thinking模式: $THINKING_MODE"
echo "原因: $REASON"
echo ""
echo -e "${YELLOW}确认切换?${NC} [y/n]"
echo "y - 确认切换到 $SUGGESTED_MODEL，并设置 thinking $THINKING_MODE"
echo "n - 保持当前模型"
