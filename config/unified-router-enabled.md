# 统一智能路由系统 - 启用状态

## 启用时间
2026-02-16 19:52

## 核心改进

### 统一分级（L1-L5）
所有4个模型（ds/kimi/glm/k2p5）统一使用相同的难度分级系统，但根据模型能力设置不同的thinking上限：

| 难度 | ds | kimi | glm | k2p5 |
|------|----| -----| -----| -----|
| L1极简 | off | off | off | off |
| L2简单 | off | concise | concise | concise |
| L3中等 | concise | concise | on | on |
| L4困难 | on | on | on | on |
| L5极难 | on | on | on | stream |

### 路由逻辑优化

```流
输入 → 判断难度(L1-L5) → 选模型 → 设thinking模式 → 等确认 → 执行
                              ↓
                    任务类型评估：
                    - 图片/文档 → kimi
                    - 代码复杂 → k2p5
                    - 中文优化 → glm
                    - 其他 → ds
```

## 适用场景

所有类型：
- ✅ 简单会话（L1，all off）- 快速响应
- ✅ 代码开发（L2-L4，动态thinking）- 省时/省成本
- ✅ 架构设计（L4-L5，on/stream）- 深度推理
- ✅ 文档分析（kimi, L3+ on）- 256k强大

## 文件

- 规则定义: config/unified-difficulty-rules.md
- 路由脚本: scripts/smart-router-unified.sh
- 启用状态: config/unified-router-enabled.md

## 使用

运行统一路由脚本：
```bash
/root/.openclaw/workspace/scripts/smart-router-unified.sh "你的输入" "当前模型"
```

或智能路由在对话中自动触发。
