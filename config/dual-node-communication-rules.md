# 双节点通信消息类型规范
# 区分是否使用AI生成，优化Token消耗

## 消息类型定义

### 0 Token - 纯数据交换（禁止使用AI生成）
- `heartbeat` - 心跳保活
- `status_report` - 状态汇报
- `task_progress` - 任务进度
- `system_alert` - 系统告警（模板化）
- `data_sync` - 数据同步

### 低Token - 模板填充
- `task_assign` - 任务分配（预定义模板）
- `result_report` - 结果汇报（结构化数据）
- `error_notify` - 错误通知（关键信息）

### 正常Token - AI生成（限制使用）
- `deep_chat` - 深度交流
- `decision_making` - 决策讨论
- `problem_solving` - 问题解决
- `user_request` - 用户明确要求

## 对话触发规则

### 必须AI对话的情况
1. 需要决策判断
2. 遇到新问题
3. 异常情况处理
4. 用户明确要求

### 禁止AI对话的情况
1. 状态汇报 → 使用JSON
2. 进度更新 → 使用模板
3. 心跳检查 → 纯ping/pong
4. 已知问题例行处理 → 自动化

## 静默检测机制

```python
HEARTBEAT_INTERVAL = 1800  # 30分钟
SILENCE_THRESHOLD = 5400   # 90分钟无AI对话

# 每30分钟纯数据心跳（0 token）
# 连续3次心跳无响应 → AI生成告警
```

## Token消耗预算

| 类型 | 每小时预算 | 说明 |
|-----|-----------|------|
| 纯数据通信 | 0 tokens | 心跳、状态、进度 |
| 模板消息 | 100 tokens | 任务分配、结果汇报 |
| AI对话 | 1000 tokens | 深度交流、决策讨论 |
| **总计** | **1100 tokens/小时** | 较之前降低93% |

## 实施时间
- 立即生效
- 备用节点需同步更新
