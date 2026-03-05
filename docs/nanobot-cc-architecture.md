# Nanobot Command Center - 架构文档

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    🤖 Command Center (指挥中心)                   │
│                         Port: 18789                              │
│                    Token: cc-token-xxx                          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Bot Relay Controller                        │   │
│  │         (nb-relay.py / nanobot-cc.sh)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              │ Bot Relay Protocol               │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Feishu Bot (消息同步)                        │   │
│  │         重要消息回流到飞书机器人                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
   ┌──────────┐        ┌──────────┐        ┌──────────┐
   │  NB01    │        │  NB02    │        │  NB03    │
   │Port:18801│        │Port:18802│        │Port:18803│
   │Token:xxx │        │Token:xxx │        │Token:xxx │
   └──────────┘        └──────────┘        └──────────┘
         │                    │                    │
   ┌──────────┐        ┌──────────┐        ┌──────────┐
   │  NB04    │        │  NB05    │        │  NB06    │
   │Port:18804│        │Port:18805│        │Port:18806│
   └──────────┘        └──────────┘        └──────────┘
         │                    │                    │
   ┌──────────┐        ┌──────────┐        ┌──────────┐
   │  NB07    │        │  NB08    │        │  NB09    │
   │Port:18807│        │Port:18808│        │Port:18809│
   └──────────┘        └──────────┘        └──────────┘
                              │
                        ┌──────────┐
                        │  NB10    │
                        │Port:18810│
                        └──────────┘
```

## 节点配置

| 节点 | Gateway端口 | Token | API Key |
|------|-------------|-------|---------|
| NB01 | 18801 | nb01-token-xxx | nvapi-KK5wL7... |
| NB02 | 18802 | nb02-token-xxx | nvapi-J3b15L... |
| NB03 | 18803 | nb03-token-xxx | nvapi-IPtXI8... |
| NB04 | 18804 | nb04-token-xxx | nvapi-K7bWEy... |
| NB05 | 18805 | nb05-token-xxx | nvapi-NQj1GH... |
| NB06 | 18806 | nb06-token-xxx | nvapi-CvbuEv... |
| NB07 | 18807 | nb07-token-xxx | nvapi-gWHf6K... |
| NB08 | 18808 | nb08-token-xxx | nvapi-oyDy6F... |
| NB09 | 18809 | nb09-token-xxx | nvapi-RBDc9C... |
| NB10 | 18810 | nb10-token-xxx | nvapi-BzaCTX... |

每个节点配置：
- 4个模型: GLM 4.7, Kimi K2.5, DeepSeek V3.2, Step 3.5 Flash
- 独立workspace: `/root/.openclaw/workspace/nanobots/nbXX/`
- 独立gateway端口和token
- 独立NVIDIA API Key

## 指挥方式

### 1. 通过 Bot Relay 直接指挥

```bash
# 检查所有节点状态
python3 scripts/nb-relay.py status

# 发送消息到指定节点
python3 scripts/nb-relay.py send NB01 "任务内容" glm

# 广播到所有节点
python3 scripts/nb-relay.py broadcast "任务内容" kimi

# 与指定节点对话
python3 scripts/nb-relay.py chat NB01
```

### 2. 通过管理脚本控制

```bash
# 启动所有节点
./scripts/nanobot-cc.sh start

# 停止所有节点
./scripts/nanobot-cc.sh stop

# 查看状态
./scripts/nanobot-cc.sh status

# 测试连接
./scripts/nanobot-cc.sh test

# 执行relay命令
./scripts/nanobot-cc.sh cmd send NB01 "Hello"
```

## 飞书消息同步

通过 `feishu-notify.py` 将重要消息同步到飞书：

| 级别 | 触发条件 | 同步方式 |
|------|----------|----------|
| CRITICAL | 节点离线/任务失败 | 立即推送 |
| HIGH | 任务完成 | 实时推送 |
| NORMAL | 状态更新 | 批量汇总 |

```bash
# 节点状态变更通知
python3 scripts/feishu-notify.py node-status NB01 offline

# 任务完成通知
python3 scripts/feishu-notify.py task-done NB01 task-001 30

# 发送自定义消息
python3 scripts/feishu-notify.py text "重要消息"
```

## 文件结构

```
workspace/
├── command-center/
│   └── openclaw.json          # 指挥中心配置
├── nanobots/
│   ├── nb01/openclaw.json     # NB01独立配置
│   ├── nb02/openclaw.json     # NB02独立配置
│   ├── ...
│   └── nb10/openclaw.json     # NB10独立配置
├── scripts/
│   ├── nb-relay.py            # Bot Relay控制器
│   ├── nanobot-cc.sh          # 管理脚本
│   └── feishu-notify.py       # 飞书通知器
└── logs/                      # 日志目录
```

## 工作流程

1. **启动阶段**: 运行 `./scripts/nanobot-cc.sh start` 启动10个节点
2. **指挥阶段**: 通过 `nb-relay.py` 发送命令到指定节点或广播
3. **同步阶段**: 重要消息自动同步到飞书机器人
4. **监控阶段**: 通过 `status` 命令查看节点健康状态

## API调用方式

每个节点独立调用NVIDIA Build API：

```python
import requests

# NB01调用示例
headers = {"Authorization": "Bearer nvapi-KK5wL7..."}
payload = {
    "model": "z-ai/glm4.7",
    "messages": [{"role": "user", "content": "Hello"}]
}
resp = requests.post(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers=headers,
    json=payload
)
```

---
创建时间: 2026-03-05
版本: v1.0
