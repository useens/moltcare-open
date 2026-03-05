# OpenClaw Command Center - 指挥中心架构

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    🎯 Command Center                         │
│                    指挥中心 (主节点)                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Bot Relay    │  │ Feishu Sync  │  │ Node Manager     │  │
│  │ 消息转发      │  │ 飞书同步      │  │ 节点管理器        │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                  │                    │            │
│         └──────────────────┼────────────────────┘            │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐        ┌─────────┐          ┌─────────┐
   │  NB01   │        │  NB02   │  ......  │  NB10   │
   │ :18801  │        │ :18802  │          │ :18810  │
   └─────────┘        └─────────┘          └─────────┘
   独立AI Agent       独立AI Agent         独立AI Agent
   (独立API Key)      (独立API Key)        (独立API Key)
```

## 节点配置

| 节点 | Gateway端口 | API Key | 模型 |
|------|-------------|---------|------|
| NB01 | 18801 | KK5wL7... | GLM/Kimi/DS/Step |
| NB02 | 18802 | J3b15L... | GLM/Kimi/DS/Step |
| NB03 | 18803 | IPtXI8... | GLM/Kimi/DS/Step |
| NB04 | 18804 | K7bWEy... | GLM/Kimi/DS/Step |
| NB05 | 18805 | NQj1GH... | GLM/Kimi/DS/Step |
| NB06 | 18806 | CvbuEv... | GLM/Kimi/DS/Step |
| NB07 | 18807 | gWHf6K... | GLM/Kimi/DS/Step |
| NB08 | 18808 | oyDy6F... | GLM/Kimi/DS/Step |
| NB09 | 18809 | RBDc9C... | GLM/Kimi/DS/Step |
| NB10 | 18810 | BzaCTX... | GLM/Kimi/DS/Step |

## 核心组件

### 1. Bot Relay (`bot-relay.py`)
负责与10个nanobot节点通信:
- 状态检查
- 消息转发
- 任务分发

### 2. Feishu Sync (`feishu-sync.py`)
将重要消息同步到飞书:
- 节点上下线通知
- 任务完成/失败通知
- 定时心跳

### 3. Node Manager
管理节点配置和调度策略

## 飞书同步规则

| 级别 | 触发条件 | 同步方式 |
|------|----------|----------|
| 🚨 CRITICAL | 节点离线/任务失败 | 立即推送 |
| 🔔 HIGH | 节点上线/任务完成 | 实时推送 |
| ℹ️ NORMAL | 常规状态 | 汇总报告 |
| 📝 LOW | 心跳/调试 | 每小时汇总 |

## 使用指南

### 查看节点状态

```bash
cd /root/.openclaw/workspace/command-center
python3 bot-relay.py status
```

### 向指定节点发送消息

```bash
python3 bot-relay.py send NB01 "你好，请介绍一下自己" --model glm
```

可选模型:
- `glm` - GLM 4.7
- `kimi` - Kimi K2.5
- `ds` - DeepSeek V3.2
- `step` - Step 3.5 Flash

### 广播消息到所有节点

```bash
python3 bot-relay.py broadcast "请总结今天的工作" --model kimi
```

### 与节点交互模式

```bash
python3 bot-relay.py chat NB01
```

### 发送测试消息到飞书

```bash
python3 feishu-sync.py test
```

### 查看同步日志

```bash
python3 feishu-sync.py logs
```

## 文件结构

```
command-center/
├── openclaw.json           # 指挥中心配置
├── bot-relay.py           # Bot Relay主程序
├── feishu-sync.py         # 飞书同步模块
└── sync.log               # 同步日志

nanobots/
├── nb01/openclaw.json     # NB01独立配置
├── nb02/openclaw.json     # NB02独立配置
├── ...
└── nb10/openclaw.json     # NB10独立配置
```

## 启动命令

### 启动单个nanobot节点

```bash
# NB01
export OPENCLAW_CONFIG=/root/.openclaw/workspace/nanobots/nb01/openclaw.json
openclaw gateway start

# NB02
export OPENCLAW_CONFIG=/root/.openclaw/workspace/nanobots/nb02/openclaw.json
openclaw gateway start --port 18802
```

### 启动所有节点（批量）

```bash
cd /root/.openclaw/workspace/command-center
python3 start-nodes.py
```

## API调用示例

### 直接调用节点API

```bash
# NB01
API_KEY="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"
curl -X POST https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "z-ai/glm4.7",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---
生成时间: 2026-03-05
版本: v1.0
