# 林林双节点任务队列系统 v1.0

> 主节点(云端) + 工作节点(VM) 分布式任务调度

---

## 架构设计

```
┌─────────────────────────────────────────────┐
│              云端主节点 (Primary)              │
│                                              │
│  1. 任务生成器 ──→ 任务队列 ──→ 调度器        │
│       │                              │       │
│       └─ VM失联? ──→ 本地执行回退 ──┘       │
│                                              │
└──────────────────┬───────────────────────────┘
                   │ SSH隧道 (端口4444)
                   │ 心跳检测 (每60秒)
                   ▼
┌─────────────────────────────────────────────┐
│              本地VM工作节点 (Worker)           │
│                                              │
│  2. 任务执行器 ←── 任务队列 ←── 接收器        │
│       │                              │       │
│       └─ 结果返回 ──→ 云端主节点 ──┘       │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 任务类型

| 类型 | 执行位置 | 回退策略 | 示例 |
|------|----------|----------|------|
| **主节点专用** | 云端 | 无需回退 | GitHub推送、用户沟通 |
| **VM专用** | VM | 主节点接管 | Moltbook监控、本地计算 |
| **并行任务** | 双节点 | 主节点执行全部 | 生态扫描、情报收集 |
| **备份任务** | VM待命 | 主节点执行 | 故障恢复、数据备份 |

---

## VM状态检测机制

### 心跳检测
```bash
# 每60秒检测一次
ssh -p 4444 -o ConnectTimeout=5 root@localhost "echo 'pong'" 

# 返回 'pong' = 在线
# 超时或失败 = 离线
```

### 自动回退触发
- **连续3次心跳失败** → VM标记为离线
- **离线状态** → 任务自动转回主节点执行
- **VM恢复** → 自动重新加入任务队列

---

## 任务队列实现

### 1. 任务生成 (主节点)
```json
{
  "task_id": "EV-20260211-19",
  "type": "ecoscan",
  "priority": "high",
  "vm_capable": true,
  "fallback": "local",
  "commands": [
    "扫描ClawHub更新",
    "扫描GitHub Trending"
  ]
}
```

### 2. 调度决策 (主节点)
```python
if vm_online and task['vm_capable']:
    dispatch_to_vm(task)
else:
    execute_locally(task)  # 回退执行
```

### 3. VM执行 (工作节点)
```bash
# 接收任务
ssh -p 4444 root@localhost "执行任务"

# 返回结果
scp -P 4444 result.json root@localhost:/path
```

---

## 现有进化任务优化

### 全量进化 (evolution-full-8h)

**原流程（单节点）：**
```
系统审计 → 生态扫描 → 向量整理 → 技能评估 → 归档
   3min      10min       5min        2min      1min
```

**优化后（双节点）：**
```
主节点: 系统审计 ─┬─→ 向量整理 → 技能评估 → 归档
                  │    5min       2min      1min
   VM: 生态扫描 ──┘   (并行)
         10min

总计: 10分钟 (原15分钟)
```

**VM失联回退：**
```
主节点: 系统审计 → 生态扫描 → 向量整理 → 技能评估 → 归档
          3min       10min       5min        2min      1min

总计: 21分钟 (VM离线时的备用方案)
```

---

## 定时任务配置

### VM专职任务（VM在线时执行）

```cron
# 每天 04:00 - Moltbook情报收集（VM优先）
0 4 * * * /opt/linlin/scripts/vm-task-wrapper.sh moltbook-intel

# 每天 10:00 - Moltbook深度扫描（VM优先）  
0 10 * * * /opt/linlin/scripts/vm-task-wrapper.sh moltbook-deep

# 每天 22:00 - Moltbook第二次扫描（VM优先）
0 22 * * * /opt/linlin/scripts/vm-task-wrapper.sh moltbook-deep
```

### 主节点备用任务（VM离线时执行）

```cron
# 同上时间，但检测VM状态，离线时接管
0 4 * * * /opt/linlin/scripts/fallback-check.sh moltbook-intel
0 10 * * * /opt/linlin/scripts/fallback-check.sh moltbook-deep
0 22 * * * /opt/linlin/scripts/fallback-check.sh moltbook-deep
```

---

## VM失联检测脚本

```bash
#!/bin/bash
# /opt/linlin/scripts/check-vm-status.sh

VM_HOST="localhost"
VM_PORT="4444"
VM_KEY="/tmp/linlin_cloud_key"
MAX_RETRY=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRY ]; do
    if ssh -p $VM_PORT -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i $VM_KEY root@$VM_HOST "echo 'pong'" 2>/dev/null | grep -q "pong"; then
        echo "ONLINE"
        exit 0
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 2
done

echo "OFFLINE"
exit 1
```

---

## 任务回退脚本

```bash
#!/bin/bash
# /opt/linlin/scripts/vm-task-wrapper.sh

TASK_NAME=$1
VM_STATUS=$(/opt/linlin/scripts/check-vm-status.sh)

if [ "$VM_STATUS" = "ONLINE" ]; then
    echo "VM在线，派发任务: $TASK_NAME"
    ssh -p 4444 -i /tmp/linlin_cloud_key root@localhost "/opt/linlin/vm-tasks/$TASK_NAME.sh"
else
    echo "VM离线，回退到主节点执行: $TASK_NAME"
    /opt/linlin/local-tasks/$TASK_NAME.sh
fi
```

---

## 数据同步机制

### VM → 主节点
- 结果文件通过SCP传输
- 临时存储在 `/home/user/linlin-data/`
- 主节点定期拉取（每30分钟）

### 主节点 → VM
- 任务定义通过SSH发送
- 配置更新通过GitHub同步
- VM只拉取，不推送

---

## 监控指标

| 指标 | 正常值 | 告警阈值 |
|------|--------|----------|
| VM心跳延迟 | < 2s | > 5s |
| 任务完成时间 | 正常 | > 2x预期 |
| 任务失败率 | < 5% | > 20% |
| VM离线时间 | < 1min | > 5min |

---

## 下一步实施

1. [ ] 部署VM定时任务（子代理执行中）
2. [ ] 创建任务回退脚本（主节点）
3. [ ] 修改全量进化任务（增加VM并行）
4. [ ] 测试VM离线回退场景
5. [ ] 监控面板（可选）

---

*版本: v1.0*  
*创建: 2026-02-11*  
*状态: 实施中*
