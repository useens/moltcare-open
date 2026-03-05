# OpenClaw Command Center 部署完成

## 部署时间
2026-03-05 22:55

## 节点状态
✅ 所有10个节点在线 (10/10)

| 节点 | 状态 | 模型数 |
|------|------|--------|
| NB01 | ✅ 在线 | 187 |
| NB02 | ✅ 在线 | 187 |
| NB03 | ✅ 在线 | 187 |
| NB04 | ✅ 在线 | 187 |
| NB05 | ✅ 在线 | 187 |
| NB06 | ✅ 在线 | 187 |
| NB07 | ✅ 在线 | 187 |
| NB08 | ✅ 在线 | 187 |
| NB09 | ✅ 在线 | 187 |
| NB10 | ✅ 在线 | 187 |

## 核心组件

### 1. 节点管理器 (cc-node-manager.py)
- 监控10个nanobot节点状态
- 支持轮询和随机负载均衡
- 实时健康检查

### 2. 消息中继 (cc-relay-hub.py)
- 4级消息分级: CRITICAL/HIGH/NORMAL/LOW
- CRITICAL/HIGH: 立即同步到飞书
- NORMAL: 批量汇总(5分钟)
- LOW: 不同步

### 3. 飞书通知器 (feishu-notify.py)
- 节点状态变更通知
- 任务完成/失败通知
- 心跳消息
- 批量汇总报告

### 4. 主控制器 (cc.py)
- 统一入口
- 状态监控面板
- 任务分发

## 可用命令

```bash
# 查看状态
python3 scripts/cc.py status

# 发送任务到指定节点
python3 scripts/cc.py task NB01 "任务内容" --model glm

# 广播任务到所有节点
python3 scripts/cc.py broadcast "任务内容" --model kimi

# 查看消息日志
python3 scripts/cc.py relay

# 发送测试消息
python3 scripts/feishu-notify.py test

# 节点状态
python3 scripts/cc-node-manager.py status

# 监控面板
python3 scripts/cc.py dashboard
```

## 配置文件

- 主配置: `/root/.openclaw/openclaw.json`
- 节点配置: `config/nanobot-models-10.json`
- 定时任务: `config/cc-cron.txt`
- 架构文档: `docs/command-center-architecture.md`
- 使用指南: `docs/command-center-readme.md`

## 飞书同步规则

| 级别 | 触发条件 | 同步方式 |
|------|----------|----------|
| CRITICAL | 节点故障/任务失败 | 立即推送 |
| HIGH | 任务完成/重要事件 | 实时推送 |
| NORMAL | 常规状态更新 | 批量汇总(5分钟) |
| LOW | 调试信息 | 不同步 |

## 定时任务

```cron
# 每5分钟检查节点状态
*/5 * * * * python3 scripts/cc-node-manager.py status

# 每15分钟发送心跳
*/15 * * * * python3 scripts/feishu-notify.py heartbeat

# 每小时汇总报告
0 * * * * python3 scripts/cc-relay-hub.py logs 50
```

---
✅ 指挥中心已就绪，可通过飞书机器人接收重要消息
