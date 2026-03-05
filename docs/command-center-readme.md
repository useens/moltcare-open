# OpenClaw Command Center

OpenClaw指挥中心架构 - 用于统一管理10个nanobot节点，并通过飞书机器人同步重要消息。

## 架构概览

```
┌─────────────────────────────────────────┐
│         Command Center (指挥中心)        │
│         当前节点: instance-main          │
├─────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌───────────┐ │
│  │ Node    │ │ Relay   │ │ Feishu    │ │
│  │ Manager │ │ Hub     │ │ Notifier  │ │
│  └────┬────┘ └────┬────┘ └─────┬─────┘ │
│       │           │            │       │
│       └───────────┼────────────┘       │
│                   │                    │
│  ┌────────────────┴────────────────┐  │
│  │         10 Nanobot Nodes         │  │
│  │  NB01-NB10 (nvidia-build-nb*)   │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 快速开始

### 1. 查看节点状态

```bash
python3 scripts/cc.py status
```

或直接使用节点管理器:

```bash
python3 scripts/cc-node-manager.py status
```

### 2. 发送任务到指定节点

```bash
python3 scripts/cc.py task NB01 "你的任务提示词" --model glm
```

可用模型:
- `glm` - GLM 4.7
- `kimi` - Kimi K2.5
- `ds` - DeepSeek V3.2
- `step` - Step 3.5 Flash

### 3. 广播任务到所有节点

```bash
python3 scripts/cc.py broadcast "你的任务提示词" --model kimi
```

### 4. 查看消息日志

```bash
python3 scripts/cc.py relay
```

### 5. 发送测试消息到飞书

```bash
python3 scripts/feishu-notify.py test
```

## 节点配置

10个nanobot节点配置如下:

| 节点 | Provider | API Key前缀 | 模型 |
|------|----------|-------------|------|
| NB01 | nvidia-build-nb01 | KK5wL7... | GLM/Kimi/DS/Step |
| NB02 | nvidia-build-nb02 | J3b15L... | GLM/Kimi/DS/Step |
| NB03 | nvidia-build-nb03 | IPtXI8... | GLM/Kimi/DS/Step |
| NB04 | nvidia-build-nb04 | K7bWEy... | GLM/Kimi/DS/Step |
| NB05 | nvidia-build-nb05 | NQj1GH... | GLM/Kimi/DS/Step |
| NB06 | nvidia-build-nb06 | CvbuEv... | GLM/Kimi/DS/Step |
| NB07 | nvidia-build-nb07 | gWHf6K... | GLM/Kimi/DS/Step |
| NB08 | nvidia-build-nb08 | oyDy6F... | GLM/Kimi/DS/Step |
| NB09 | nvidia-build-nb09 | RBDc9C... | GLM/Kimi/DS/Step |
| NB10 | nvidia-build-nb10 | BzaCTX... | GLM/Kimi/DS/Step |

## 消息同步规则

| 级别 | 触发条件 | 同步方式 |
|------|----------|----------|
| CRITICAL | 节点故障/任务失败 | 立即推送到飞书 |
| HIGH | 任务完成/重要事件 | 实时推送到飞书 |
| NORMAL | 常规状态更新 | 批量汇总(5分钟) |
| LOW | 调试信息 | 不同步 |

## 定时任务

配置在 `config/cc-cron.txt`:

- 每5分钟: 检查节点状态
- 每15分钟: 发送心跳到飞书
- 每小时: 生成汇总报告
- 每天凌晨3点: 清理旧日志

安装定时任务:

```bash
crontab config/cc-cron.txt
```

## 文件结构

```
workspace/
├── scripts/
│   ├── cc.py                    # 主控制器
│   ├── cc-node-manager.py       # 节点管理器
│   ├── cc-relay-hub.py          # 消息中继
│   └── feishu-notify.py         # 飞书通知器
├── config/
│   ├── nanobot-models-10.json   # 10节点模型配置
│   ├── openclaw-nanobot.json    # OpenClaw主配置
│   └── cc-cron.txt              # 定时任务配置
├── docs/
│   └── command-center-architecture.md  # 架构文档
└── logs/                         # 日志目录
    ├── relay-hub.log
    ├── node-check.log
    └── heartbeat.log
```

## 监控面板

启动实时监控:

```bash
python3 scripts/cc.py dashboard
```

按 `Ctrl+C` 退出。

## 故障排除

### 节点离线

1. 检查API Key是否有效:
   ```bash
   curl -H "Authorization: Bearer nvapi-xxx" https://integrate.api.nvidia.com/v1/models
   ```

2. 检查网络连接

3. 查看详细日志:
   ```bash
   tail -f logs/node-check.log
   ```

### 飞书消息未收到

1. 检查飞书配置:
   ```bash
   python3 scripts/feishu-notify.py test
   ```

2. 验证channel配置:
   ```bash
   openclaw config get channels.feishu
   ```

## 扩展

### 添加新节点

1. 在 `cc-node-manager.py` 中添加节点配置
2. 在 `openclaw.json` 中添加provider配置
3. 重启OpenClaw服务

### 自定义消息规则

修改 `cc-relay-hub.py` 中的 `_send_immediate` 和 `_batch_send` 方法。

---

生成时间: 2026-03-05
版本: v1.0
