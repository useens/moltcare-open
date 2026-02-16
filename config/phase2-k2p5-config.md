# 第二阶段配置：k2p5基础切换

## 目标
1. k2p5 默认 reasoning: off
2. 支持手动升级 thinking 模式

## 模型信息
- 名称：kimi-coding/k2p5
- 别名：k2p5
- 费用：付费
- 默认：reasoning off

## Thinking 分级配置

| 级别 | 触发条件 | reasoning模式 | 使用场景 |
|------|---------|--------------|---------|
| L1 简单 | 语法检查、代码片段、单行问题 | off | 最省钱，快速响应 |
| L2 中等 | 函数编写、模块设计、常规调试 | concise | 平衡效率 |
| L3 困难 | 架构设计、复杂算法、系统重构 | on | 完整推理 |
| L4 极难 | 跨系统架构、性能优化、疑难bug | stream | 过程透明 |

## 手动切换指令

用户可通过以下指令手动调整：
- `/thinking off` - 关闭思考
- `/thinking concise` - 精简思考
- `/thinking on` - 完整思考
- `/thinking stream` - 流式思考

## 下一步
现在切换到k2p5模型并测试thinking配置。
