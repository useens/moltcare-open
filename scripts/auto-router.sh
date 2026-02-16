#!/bin/bash
# 自动路由脚本
# 根据用户输入自动推荐模型

# 获取用户输入
USER_INPUT="$1"
CURRENT_MODEL="$2"  # 当前模型，用于判断是否需要切换

# 初始化
SUGGESTED_MODEL=""
REASON=""
CONFIDENCE=0  # 置信度 0-100

# 检查是否明确指定模型
if echo "$USER_INPUT" | grep -qiE "(切换到|使用|换到|改为).*(k2p5|kimi|glm|ds)"; then
    # 用户明确指定，不干预
    if echo "$USER_INPUT" | grep -qi "k2p5"; then
        echo "{\"action\": \"none\", \"reason\": \"用户明确指定k2p5\"}"
    elif echo "$USER_INPUT" | grep -qi "kimi"; then
        echo "{\"action\": \"none\", \"reason\": \"用户明确指定kimi\"}"
    elif echo "$USER_INPUT" | grep -qi "glm"; then
        echo "{\"action\": \"none\", \"reason\": \"用户明确指定glm\"}"
    elif echo "$USER_INPUT" | grep -qi "ds"; then
        echo "{\"action\": \"none\", \"reason\": \"用户明确指定ds\"}"
    fi
    exit 0
fi

# 1. 检测图片/长文档 → kimi（高优先级）
if echo "$USER_INPUT" | grep -qiE "(图片|截图|照片|图像|文档|pdf|长文|整本书|分析图表|读取文件)"; then
    SUGGESTED_MODEL="kimi"
    REASON="检测到图片或长文档分析需求"
    CONFIDENCE=90
fi

# 2. 检测代码任务 → k2p5（中优先级）
if [ -z "$SUGGESTED_MODEL" ] && echo "$USER_INPUT" | grep -qiE "(代码|编程|函数|类|模块|bug|调试|报错|修复|算法|架构|重构|Python|JavaScript|Java|Go|Rust|API|接口|数据库|SQL)"; then
    SUGGESTED_MODEL="k2p5"
    REASON="检测到代码开发任务"
    CONFIDENCE=85
fi

# 3. 检测中文优化 → glm（低优先级）
if [ -z "$SUGGESTED_MODEL" ] && echo "$USER_INPUT" | grep -qiE "(中文|本地化|翻译|文案|快速响应)"; then
    SUGGESTED_MODEL="glm"
    REASON="检测到中文处理需求"
    CONFIDENCE=70
fi

# 4. 默认 → ds
if [ -z "$SUGGESTED_MODEL" ]; then
    SUGGESTED_MODEL="ds"
    REASON="默认通用模型"
    CONFIDENCE=50
fi

# 检查是否与当前模型相同
if [ "$SUGGESTED_MODEL" = "$CURRENT_MODEL" ]; then
    echo "{\"action\": \"none\", \"reason\": \"当前模型已是最优选择\", \"model\": \"$SUGGESTED_MODEL\"}"
    exit 0
fi

# 输出建议
echo "{"
echo "  \"action\": \"suggest\","
echo "  \"current_model\": \"$CURRENT_MODEL\","
echo "  \"suggested_model\": \"$SUGGESTED_MODEL\","
echo "  \"reason\": \"$REASON\","
echo "  \"confidence\": $CONFIDENCE,"
echo "  \"need_confirmation\": true"
echo "}"
