# OpenClaw 指挥中心架构

## 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      指挥中心 (Command Center)                   │
│                   当前节点: instance-20250227-023059            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Feishu Bot   │  │ Gateway      │  │ Task Scheduler       │  │
│  │ 消息同步      │  │ ws://:18789  │  │ 任务调度器            │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         └─────────────────┼──────────────────────┘              │
│                           │                                     │
│         ┌─────────────────┴─────────────────┐                   │
│         ▼                                   ▼                   │
│  ┌─────────────┐                    ┌──────────────┐           │
│  │ Node Manager│                    │ Relay Hub    │           │
│  │ 节点管理器   │                    │ 中继中心      │           │
│  └──────┬──────┘                    └──────┬───────┘           │
│         │                                  │                    │
└─────────┼──────────────────────────────────┼────────────────────┘
          │                                  │
          ▼                                  ▼
    ┌─────────────┐                  ┌─────────────┐
    │ 10 Nanobot  │                  │ Bot Relay   │
    │ 工作节点     │                  │ 消息转发    │
    │             │                  │             │
    │ NB01-NB10   │                  │ 飞书通知    │
    └─────────────┘                  └─────────────┘
```

## 节点配置

| 节点ID | Provider | 模型 | 状态 |
|--------|----------|------|------|
| NB01 | nvidia-build-nb01 | GLM 4.7 / Kimi 2.5 / DeepSeek V3.2 / Step 3.5 | ✅ 已配置 |
| NB02 | nvidia-build-nb02 | GLM 4.7 / Kimi 2.5 / DeepSeek V3.2 / Step 3.5 | ✅ 已配置 |
| NB03 | nvidia-build-nb03 | GLM 4.7 / Kimi 2.5 / DeepSeek V3.2 / Step 3.5 | ✅ 已配置 |
| NB04 | nvidia-build-nb04 | GLM 4.7 / Kimi 2.5 / DeepSeek V3.2 / Step 3.5 | ✅ 已配置 |
| NB05 | nvidia-build-nb05 | GLM 4.7 / Kimi 2.5 / DeepSeek V3.2 / Step 3.5 | ✅ 已配置 |
| NB06 | nvidia-build-nb06 | GLM 4.7 / Kimi 2.5 / DeepSeek V3.2 / Step 3.5 | ✅ 已配置 |
| NB07 | nvidia-build-nb07 | GLM 4.7 / Kimi 2.5 / DeepSeek V3.2 / Step 3.5 | ✅ 已配置 |
| NB08 | nvidia-build-nb08 | GLM 4.7 / Kimi 2.5 / DeepSeek V3.2 / Step 3.5 | ✅ 已配置 |
| NB09 | nvidia-build-nb09 | GLM 4.7 / Kimi 2.5 / DeepSeek V3.2 / Step 3.5 | ✅ 已配置 |
| NB10 | nvidia-build-nb10 | GLM 4.7 / Kimi 2.5 / DeepSeek V3.2 / Step 3.5 | ✅ 已配置 |

## 核心组件

### 1. Node Manager (节点管理器)
- 监控10个节点状态
- 负载均衡任务分配
- 节点健康检查

### 2. Relay Hub (中继中心)
- 汇总各节点消息
- 消息分级过滤
- 飞书同步推送

### 3. Task Scheduler (任务调度器)
- 并行任务分发
- 结果聚合
- 故障转移

## 飞书同步规则

| 级别 | 触发条件 | 同步方式 |
|------|----------|----------|
| CRITICAL | 节点故障/任务失败 | 立即推送 |
| HIGH | 任务完成/重要事件 | 实时推送 |
| NORMAL | 常规状态更新 | 批量汇总(5分钟) |
| LOW | 调试信息 | 不同步 |

## 配置文件

- 主配置: `/root/.openclaw/openclaw.json`
- 节点配置: `config/nanobot-models-10.json`
- 指挥中心: `config/command-center.yaml`

## 使用方式

```bash
# 查看节点状态
python3 scripts/cc-node-manager.py status

# 发送任务到指定节点
python3 scripts/cc-node-manager.py task --node NB01 --prompt "任务内容"

# 广播任务到所有节点
python3 scripts/cc-node-manager.py broadcast --prompt "任务内容"

# 查看飞书同步日志
python3 scripts/cc-relay-hub.py logs
```

---
生成时间: 2026-03-05
版本: v1.0
