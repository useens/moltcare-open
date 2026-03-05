# 🤖 Nanobot Command Center - 架构完成报告

## 建设完成时间
2026-03-05 23:35

## 架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                      🤖 COMMAND CENTER 指挥中心                      │
│                         主控节点 (Port 18789)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ 📊 Dashboard │  │ 📡 Feishu   │  │ 🎯 Scheduler│  │ 🤖 Relay  │  │
│  │ 监控面板     │  │ Sync 飞书同步│  │ 任务调度器   │  │ Bot中继   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘  │
│         │                │                │               │        │
│         └────────────────┴────────────────┴───────────────┘        │
│                                    │                                │
│                                    ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     10 Nanobot Nodes                         │   │
│  │                                                              │   │
│  │   ⚡ Step 3.5 Flash 组          🧠 DeepSeek V3.2 组          │   │
│  │   ─────────────────────         ─────────────────────        │   │
│  │   NB01 ● Port 18801             NB06 ● Port 18806            │   │
│  │   NB02 ● Port 18802             NB07 ● Port 18807            │   │
│  │   NB03 ● Port 18803             NB08 ● Port 18808            │   │
│  │   NB04 ● Port 18804             NB09 ● Port 18809            │   │
│  │   NB05 ● Port 18805             NB10 ● Port 18810            │   │
│  │                                                              │   │
│  │   状态: ✅ 全部在线 (10/10)                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. Bot Relay (nb-relay.py) ✅
- **功能**: 与10个nanobot节点通信
- **命令**:
  ```bash
  python3 scripts/nb-relay.py status          # 查看节点状态
  python3 scripts/nb-relay.py send NB01 "msg" # 发送消息到NB01
  python3 scripts/nb-relay.py broadcast "msg" # 广播到所有节点
  python3 scripts/nb-relay.py chat NB01       # 与NB01对话
  ```

### 2. Feishu Sync (feishu-sync.py) ✅
- **功能**: 消息分级同步到飞书
- **级别**:
  - 🚨 CRITICAL: 立即同步 (节点离线/任务失败)
  - ⚠️ HIGH: 立即同步 (任务完成/重要事件)
  - ℹ️ NORMAL: 批量汇总 (5分钟)
  - 💬 LOW: 不同步 (调试信息)
- **命令**:
  ```bash
  python3 scripts/feishu-sync.py critical node.NB01 "节点离线"
  python3 scripts/feishu-sync.py high task.123 "任务完成"
  ```

### 3. Task Scheduler (scheduler.py) ✅
- **功能**: 智能任务调度
- **策略**:
  - `auto`: 根据任务类型自动选择
  - `step`: 使用Step组 (NB01-NB05)
  - `ds`: 使用DeepSeek组 (NB06-NB10)
  - `random`: 随机选择
- **命令**:
  ```bash
  python3 scripts/scheduler.py submit "任务" --type quick
  python3 scripts/scheduler.py stats
  ```

### 4. Dashboard (dashboard.py) ✅
- **功能**: 实时监控面板
- **命令**:
  ```bash
  python3 scripts/dashboard.py         # 启动实时监控
  python3 scripts/dashboard.py status  # 显示当前状态
  ```

### 5. Cluster Manager (nb-cluster.sh) ✅
- **功能**: 集群启停管理
- **命令**:
  ```bash
  ./scripts/nb-cluster.sh start    # 启动所有节点
  ./scripts/nb-cluster.sh stop     # 停止所有节点
  ./scripts/nb-cluster.sh restart  # 重启所有节点
  ./scripts/nb-cluster.sh status   # 查看状态
  ```

### 6. Main Controller (cc) ✅
- **功能**: 统一入口
- **命令**:
  ```bash
  ./scripts/cc status      # 系统状态
  ./scripts/cc dashboard   # 监控面板
  ./scripts/cc submit "任务"  # 提交任务
  ./scripts/cc broadcast "任务" # 广播任务
  ./scripts/cc notify "消息" # 飞书通知
  ./scripts/cc start       # 启动集群
  ./scripts/cc stop        # 停止集群
  ```

## 节点配置

### Step 3.5 Flash 组 (⚡ 快速响应)
| 节点 | Port | 默认模型 | API Key |
|------|------|----------|---------|
| NB01 | 18801 | stepfun-ai/step-3.5-flash | KK5wL7... |
| NB02 | 18802 | stepfun-ai/step-3.5-flash | J3b15L... |
| NB03 | 18803 | stepfun-ai/step-3.5-flash | IPtXI8... |
| NB04 | 18804 | stepfun-ai/step-3.5-flash | K7bWEy... |
| NB05 | 18805 | stepfun-ai/step-3.5-flash | NQj1GH... |

### DeepSeek V3.2 组 (🧠 深度推理)
| 节点 | Port | 默认模型 | API Key |
|------|------|----------|---------|
| NB06 | 18806 | deepseek-ai/deepseek-v3.2 | CvbuEv... |
| NB07 | 18807 | deepseek-ai/deepseek-v3.2 | gWHf6K... |
| NB08 | 18808 | deepseek-ai/deepseek-v3.2 | oyDy6F... |
| NB09 | 18809 | deepseek-ai/deepseek-v3.2 | RBDc9C... |
| NB10 | 18810 | deepseek-ai/deepseek-v3.2 | BzaCTX... |

## 文件结构

```
workspace/
├── command-center/
│   └── openclaw.json          # 指挥中心配置
├── nanobots/
│   ├── nb01/openclaw.json     # NB01配置 (Step)
│   ├── nb02/openclaw.json     # NB02配置 (Step)
│   ├── nb03/openclaw.json     # NB03配置 (Step)
│   ├── nb04/openclaw.json     # NB04配置 (Step)
│   ├── nb05/openclaw.json     # NB05配置 (Step)
│   ├── nb06/openclaw.json     # NB06配置 (DeepSeek)
│   ├── nb07/openclaw.json     # NB07配置 (DeepSeek)
│   ├── nb08/openclaw.json     # NB08配置 (DeepSeek)
│   ├── nb09/openclaw.json     # NB09配置 (DeepSeek)
│   ├── nb10/openclaw.json     # NB10配置 (DeepSeek)
│   └── logs/                  # 节点日志
├── scripts/
│   ├── cc                     # 主控制器 (统一入口)
│   ├── nb-relay.py            # Bot Relay
│   ├── feishu-sync.py         # 飞书同步
│   ├── scheduler.py           # 任务调度器
│   ├── dashboard.py           # 监控面板
│   ├── nb-cluster.sh          # 集群管理器
│   └── feishu-notify.py       # 飞书通知器
├── config/
│   └── cc-cron.txt            # 定时任务配置
├── docs/
│   ├── nanobot-cc-build-report.md      # 本报告
│   ├── nanobot-model-assignment.md     # 模型分配文档
│   └── command-center-architecture.md  # 架构设计文档
└── logs/                      # 指挥中心日志
```

## 定时任务

```cron
# 每5分钟: 健康检查
*/5 * * * * python3 scripts/dashboard.py status

# 每10分钟: 节点状态检查
*/10 * * * * python3 scripts/nb-relay.py status

# 每15分钟: 发送心跳到飞书
*/15 * * * * python3 scripts/feishu-sync.py high heartbeat "运行正常"

# 每小时: 批量发送汇总报告
0 * * * * python3 scripts/feishu-sync.py batch

# 每天凌晨3点: 清理日志
0 3 * * * find logs -name "*.log" -mtime +7 -delete
```

## 快速开始

```bash
# 1. 查看系统状态
./scripts/cc status

# 2. 启动监控面板
./scripts/cc dashboard

# 3. 提交任务 (自动选择节点)
./scripts/cc submit "分析这段代码" --type deep

# 4. 广播到所有节点
./scripts/cc broadcast "同步更新配置"

# 5. 发送通知到飞书
./scripts/cc notify "任务已完成"
```

## 状态汇总

- ✅ 10个nanobot节点: 全部在线
- ✅ Bot Relay: 就绪
- ✅ Feishu Sync: 就绪
- ✅ Task Scheduler: 就绪
- ✅ Dashboard: 就绪
- ✅ Cluster Manager: 就绪
- ✅ Main Controller: 就绪
- ⚠️ 飞书API调用: 待验证

## 下一步建议

1. **验证飞书同步**: 运行 `python3 scripts/feishu-sync.py test`
2. **安装定时任务**: `crontab config/cc-cron.txt`
3. **测试任务调度**: `./scripts/cc submit "测试任务"`
4. **设置监控告警**: 配置节点离线自动通知

---

**建设状态**: ✅ 完成
**版本**: v1.0.0
**构建时间**: 2026-03-05
