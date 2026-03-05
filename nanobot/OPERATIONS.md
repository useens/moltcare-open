# Nanobot + OpenClaw 双框架运维方案

> 🚀 **部署日期**: 2026-03-05
> **部署者**: 森森 (OpenClaw)
> **目标**: 实现双 AI 助手互相监控、互为备份

---

## 📋 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                         人类用户                             │
│                     (监督 + 授权)                           │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
         ┌─────▼──────┐              ┌───────▼──────┐
         │  OpenClaw  │◄────────────►│   Nanobot    │
         │  (森森)    │  Bot Relay   │  (虾米派派)   │
         │  主力AI    │  127.0.0.1   │  轻量备份     │
         └─────┬──────┐  :19000      └───────┬──────┘
               │                              │
          互相监控 ◄────────────────────────► 互相监控
```

---

## 🛠️ 部署组件

| 组件 | 路径 | 状态 |
|------|------|------|
| Bot Relay | `/root/.openclaw/workspace/bot-relay/relay.py` | ✅ Active |
| Nanobot | `/root/.openclaw/workspace/nanobot/nanobot.py` | ✅ Active |
| OpenClaw→Nanobot 检查 | `/root/.openclaw/workspace/scripts/health-check-nanobot.py` | ✅ Ready |
| Nanobot→OpenClaw 检查 | `/root/.openclaw/workspace/nanobot/health-check-openclaw.py` | ✅ Ready |

---

## ⚙️ 服务管理

```bash
# 查看服务状态
systemctl --user status bot-relay
systemctl --user status nanobot

# 重启服务
systemctl --user restart bot-relay
systemctl --user restart nanobot

# 查看日志
journalctl --user -u nanobot -f
journalctl --user -u bot-relay -f
```

---

## 🔍 健康检查

### 检查频率
- 每 **5分钟** 自动运行一次
- 结果记录到日志文件

### 检查指标

| 指标 | 阈值 | 级别 |
|------|------|------|
| Nanobot 内存 | > 100MB | 预警 |
| Nanobot 内存 | > 200MB | 告警 |
| OpenClaw 内存 | > 500MB | 预警 |
| OpenClaw 内存 | > 800MB | 告警 |
| Session 文件 | > 500KB | 预警 |
| Session 文件 | > 1MB | 告警 |

### 日志位置
- OpenClaw 检查 Nanobot: `/root/.openclaw/workspace/nanobot/health-check.log`
- Nanobot 检查 OpenClaw: `/root/.openclaw/workspace/nanobot/nanobot-check.log`

---

## 📡 消息中继 API

### 发送消息
```bash
curl -X POST http://127.0.0.1:19000/message \
  -H "Content-Type: application/json" \
  -d '{"from":"openclaw","to":"nanobot","message":"Hello!"}'
```

### 轮询消息
```bash
curl http://127.0.0.1:19000/poll/nanobot
```

### 查看状态
```bash
curl http://127.0.0.1:19000/status
```

---

## 🛡️ 权限矩阵

| 操作 | OpenClaw | Nanobot | 需要授权 |
|------|----------|---------|----------|
| 查看日志 | ✅ | ✅ | ❌ |
| 运行健康检查 | ✅ | ✅ | ❌ |
| 发送消息 | ✅ | ✅ | ❌ |
| 重启服务 | ❌ | ❌ | ✅ |
| 修改配置 | ❌ | ❌ | ✅ |
| 清理 session | ❌ | ❌ | ✅ |

---

## 📝 待办事项

- [ ] 添加飞书告警通知
- [ ] 优化 Nanobot 的 Poller 逻辑
- [ ] 增加更多诊断 SOP
- [ ] 测试故障恢复流程

---

*部署完成 | 2026-03-05*
