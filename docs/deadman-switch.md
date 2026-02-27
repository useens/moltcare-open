# 死手开关系统 (Dead Man's Switch)

## 概述

自动监控系统，每3小时检测森森是否响应，如无响应则自动回滚到3小时前的状态。

## 工作原理

```
每3小时
    ↓
保存当前状态快照
    ↓
发送心跳检测
    ↓
正常 ←——→ 无响应
            ↓
        自动回滚到3小时前快照
```

## 组件

| 文件 | 用途 |
|------|------|
| `scripts/deadman-switch.sh` | 主检测脚本 |
| `config/deadman-cron.txt` | Cron定时配置 |
| `.snapshots/` | 快照存储目录 |
| `logs/deadman-switch.log` | 检测日志 |
| `logs/rollback-history.log` | 回滚历史记录 |

## 保存的内容

- **记忆系统**: `memory/` 目录（含向量记忆）
- **核心档案**: MEMORY.md, USER.md, SOUL.md, AGENTS.md, IDENTITY.md
- **配置文件**: `config/` 目录

## 使用方法

### 1. 安装Cron任务

```bash
# 添加死手开关定时任务
crontab -l > /tmp/crontab_backup
cat config/deadman-cron.txt >> /tmp/crontab_backup
crontab /tmp/crontab_backup
```

### 2. 手动测试

```bash
# 手动执行一次检测
bash scripts/deadman-switch.sh
```

### 3. 查看状态

```bash
# 查看检测日志
tail -f logs/deadman-switch.log

# 查看可用快照
ls -la .snapshots/

# 查看回滚历史
cat logs/rollback-history.log
```

## 快照策略

| 类型 | 频率 | 保留数量 |
|------|------|----------|
| 3小时快照 | 每3小时 | 最近3个 |
| 小时快照 | 每小时 | 最近24个 |
| 日清理 | 每天4:00 | 7天 |

## 回滚触发条件

1. OpenClaw网关无响应
2. OpenClaw进程不存在
3. 超过1小时无任何活动日志
4. 连续重试3次仍失败

## 手动回滚

如果需要手动恢复到某个快照：

```bash
bash scripts/deadman-switch.sh rollback snapshot_20260227_120000
```

## 安全机制

- 回滚前自动创建紧急备份
- 保留回滚历史记录
- 发送通知提醒
- 自动尝试重启服务

## 日志格式

```
[2026-02-27 19:00:00] 💾 创建状态快照: snapshot_20260227_190000
[2026-02-27 19:00:05] 💓 发送心跳检测...
[2026-02-27 19:00:06] ✅ 心跳检测通过，系统运行正常
```

## 注意事项

⚠️ **重要**:
- 首次启用后需要至少3小时才能形成有效的回滚目标
- 回滚会丢失最近3小时的数据变更
- 建议定期验证快照完整性
