#!/usr/bin/env python3
"""
子代理启动前难度评估脚本
根据任务内容自动判断难度级别（L1-L5）
"""

import sys
import re

def assess_difficulty(task_text: str) -> int:
    """
    评估任务难度
    返回：1-5 (L1-L5)

    危险操作（系统修复、配置更改、root权限）必须 L5 - 强制使用 k2p5
    """
    text = task_text.lower()
    level = 2  # 默认 L2

    # 🔥 危险操作关键词 - 直接 L5 (必须 k2p5)
    danger_patterns = [
        r'系统修复', r'系统维护', r'紧急修复', r'故障排除',
        r'配置更改', r'修改配置', r'调整配置', r'配置文件',
        r'危险操作', r'高风险', r'生产环境', r'紧急变更',
        r'git reset --hard', r'rm -rf', r'重装', r'重启网关',
        r'hyper.?evolution', r'self.?upgrade', r'evolution',
        r'assess-difficulty', r'smart.?router', r'auto.?model',
        r'evolution/strategies', r'executor.execute',
        r'root权限', r'管理员权限', r'sudo', r'systemctl',
        r'gateway restart', r'cron', r'crontab', r'备份回滚',
        r'沙箱测试', r'validator', r'validate'
    ]
    for pattern in danger_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return 5  # 强制 L5

    # L5 极难关键词
    l5_patterns = [
        r'从零设计', r'核心架构', r'大规模', r'高可用', r'容灾',
        r'疑难bug', r'深度优化', r'系统重构', r'极限', r'瓶颈',
        r'分布式系统', r'微服务架构', r'性能关键路径'
    ]
    for pattern in l5_patterns:
        if re.search(pattern, text):
            level = max(level, 5)

    # L4 困难关键词
    l4_patterns = [
        r'架构', r'设计', r'策略', r'复杂算法', r'并发',
        r'性能调优', r'微服务', r'多系统', r'集成', r'数据流',
        r'API设计', r'数据库设计', r'安全', r'监控系统'
    ]
    for pattern in l4_patterns:
        if re.search(pattern, text):
            level = max(level, 4)

    # L3 中等关键词
    l3_patterns = [
        r'函数', r'模块', r'实现', r'接口', r'调试',
        r'测试', r'优化', r'重构', r'设计模式', r'API',
        r'中间件', r'工具类', r'配置管理'
    ]
    for pattern in l3_patterns:
        if re.search(pattern, text):
            level = max(level, 3)

    # L2 简单关键词（如果已提高到L3+，不降级）
    if level <= 2:
        l2_patterns = [
            r'语法', r'报错', r'怎么写', r'示例', r'修复',
            r'简单', r'配置', r'基本概念', r'帮助', r'解释'
        ]
        for pattern in l2_patterns:
            if re.search(pattern, text):
                level = max(level, 2)
                break

    # L1 极简关键词
    l1_patterns = [
        r'你好', r'在吗', r'状态', r'当前', r'几点',
        r'日期', r'确认', r'好的', r'取消', r'是', r'否',
        r'谢谢', r'再见'
    ]
    for pattern in l1_patterns:
        if re.search(pattern, text):
            level = 1
            break

    # 长度权重
    if len(task_text) > 1000:
        level = min(5, level + 1)
    elif len(task_text) > 500:
        level = min(5, level + 0.5)

    # 上下文权重
    if re.search(r'生产环境|紧急|线上问题|架构评审', text):
        level = min(5, level + 1)

    # 降级权重
    if re.search(r'快速看一下|小问题|极简|随便问问', text):
        level = max(1, level - 1.5)
    elif re.search(r'简单问题|帮忙看看', text):
        level = max(1, level - 1)

    return int(round(level))

def get_model_for_difficulty(difficulty: int, task_text: str = "") -> str:
    """
    根据难度返回推荐的模型
    """
    # 🔥 L5 强制使用 k2p5（危险/系统操作或极难任务）
    if difficulty >= 5:
        return "kimi-coding/k2p5", "L5 系统/危险操作 - k2p5"

    # 检查是否是图片任务（图片任务次优先）
    if re.search(r'图片|截图|图像|分析图表|OCR|照片', task_text.lower()):
        return "nvidia-build/moonshotai/kimi-k2.5", "图片任务 - Kimi K2.5"

    # 根据难度选择模型
    if difficulty >= 4:
        return "kimi-coding/k2p5", "复杂任务 - k2p5"
    elif difficulty == 3:
        # L3 中等，检查是否是代码任务
        if re.search(r'代码|编程|函数|实现|算法|调试', task_text.lower()):
            return "kimi-coding/k2p5", "代码任务 - k2p5"
        else:
            return "nvidia-build/stepfun-ai/step-3.5-flash", "中等任务 - Step"
    else:
        return "nvidia-build/stepfun-ai/step-3.5-flash", "简单任务 - Step"

def get_thinking_mode(difficulty: int, model: str) -> str:
    """
    根据难度和模型返回thinking模式
    """
    level = difficulty

    # L1 极简：全部 off
    if level == 1:
        return "off"

    # L2 简单：除 k2p5 外 concise，k2p5 也 concise
    if level == 2:
        return "concise"

    # L3 中等：ds/kimi concise，k2p5/glm on
    if level == 3:
        if model in ["kimi-coding/k2p5", "nvidia-build/z-ai/glm4.7"]:
            return "on"
        else:
            return "concise"

    # L4 困难：全部 on
    if level == 4:
        return "on"

    # L5 极难：k2p5 stream，其他 on
    if level == 5:
        if model == "kimi-coding/k2p5":
            return "stream"
        else:
            return "on"

    return "off"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: assess-difficulty.py <task_text>")
        sys.exit(1)

    task_text = sys.argv[1]
    difficulty = assess_difficulty(task_text)
    model, reason = get_model_for_difficulty(difficulty, task_text)
    thinking = get_thinking_mode(difficulty, model)

    print(f"难度级别: L{difficulty}")
    print(f"推荐模型: {model}")
    print(f"Thinking模式: {thinking}")
    print(f"原因: {reason}")
