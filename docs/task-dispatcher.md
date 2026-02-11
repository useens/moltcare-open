# 双节点任务自动分发系统 - 配置文档

## 概述

本系统实现了主节点（云端）与VM工作节点（本地）之间的任务自动分发，支持智能负载均衡和故障回退。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      主节点 (云端)                               │
│                    129.154.251.13                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  scripts/task-dispatcher.sh                              │  │
│  │  - 任务分发决策                                           │  │
│  │  - VM状态检测                                            │  │
│  │  - 结果合并                                               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              │ SSH 反向隧道 (端口 4444)          │
│                              ▼                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      VM工作节点 (本地)                           │
│                  user-virtual-machine                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  /opt/linlin/task-executor.sh                            │  │
│  │  - 任务执行                                              │  │
│  │  - 结果收集                                              │  │
│  │  - 心跳上报                                              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 文件清单

### 主节点 (云端: 129.154.251.13)

| 文件 | 路径 | 说明 |
|------|------|------|
| 任务分发器 | `scripts/task-dispatcher.sh` | 核心分发逻辑 |
| SSH密钥 | `/tmp/linlin_cloud_key` | 连接VM的私钥 |
| 任务队列 | `/var/run/linlin/tasks/` | 待处理任务 |
| 结果目录 | `/var/run/linlin/results/` | 任务结果 |
| 日志文件 | `/var/log/linlin/task-dispatcher.log` | 运行日志 |

### VM节点 (本地: user-virtual-machine)

| 文件 | 路径 | 说明 |
|------|------|------|
| 任务执行器 | `/opt/linlin/task-executor.sh` | 任务执行入口 |
| 脚本目录 | `/opt/linlin/scripts/` | 本地脚本存储 |
| 结果目录 | `/var/run/linlin/results/` | 执行结果 |
| 日志文件 | `/var/log/linlin/task-executor.log` | 运行日志 |

## 快速开始

### 1. 部署任务执行器到VM

在主节点上执行：

```bash
# 确保VM可连接
ssh -o ConnectTimeout=3 -i /tmp/linlin_cloud_key -p 4444 root@user-virtual-machine "echo 'VM在线'"

# 创建VM目录结构
ssh -i /tmp/linlin_cloud_key -p 4444 root@user-virtual-machine "mkdir -p /opt/linlin /var/run/linlin/results /var/log/linlin"

# 复制执行器到VM
scp -i /tmp/linlin_cloud_key -P 4444 /opt/linlin/task-executor.sh root@user-virtual-machine:/opt/linlin/

# 设置执行权限
ssh -i /tmp/linlin_cloud_key -p 4444 root@user-virtual-machine "chmod +x /opt/linlin/task-executor.sh"
```

### 2. 主节点配置

```bash
# 设置执行权限
chmod +x scripts/task-dispatcher.sh

# 创建必要目录
mkdir -p /var/run/linlin/{tasks,results,heartbeat} /var/log/linlin

# 检查VM状态
./scripts/task-dispatcher.sh status
```

## 使用方法

### 单任务分发

```bash
# 轻量级任务 - 单节点执行（优先VM）
./scripts/task-dispatcher.sh dispatch lightweight task-001 'echo "Hello World"'

# 并行任务 - 双节点同时执行
./scripts/task-dispatcher.sh dispatch parallel task-002 '' ./scripts/test.sh

# VM专用任务 - 必须在VM执行
./scripts/task-dispatcher.sh dispatch vm-only task-003 '' ./scripts/monitor.sh
```

### 批量任务处理

创建任务文件 `tasks.txt`：

```
# 格式: type|task_id|payload|script_path
lightweight|task-001|echo "任务1"|
parallel|task-002||/opt/scripts/job.sh
vm-only|task-003||/opt/linlin/monitor.sh
lightweight|task-004|df -h|
```

执行批量处理（最大4个并发）：

```bash
./scripts/task-dispatcher.sh batch tasks.txt 4
```

### 生成子代理

```bash
# 在VM上生成子代理
./scripts/task-dispatcher.sh subagent vm "echo '子代理任务'"

# 在本地生成子代理（VM离线时回退）
./scripts/task-dispatcher.sh subagent local "echo '本地子代理'"
```

### 直接调用VM执行器

```bash
# 通过SSH直接执行VM上的任务
ssh -i /tmp/linlin_cloud_key -p 4444 root@user-virtual-machine \
    "/opt/linlin/task-executor.sh exec task-001 command 'ls -la'"

# 执行Python任务
ssh -i /tmp/linlin_cloud_key -p 4444 root@user-virtual-machine \
    "/opt/linlin/task-executor.sh exec task-002 python 'print(sum(range(100)))'"

# 执行监控任务
ssh -i /tmp/linlin_cloud_key -p 4444 root@user-virtual-machine \
    "/opt/linlin/task-executor.sh monitor"
```

## 任务类型详解

### 1. 轻量级任务 (lightweight)

- **执行策略**: 单节点执行，优先选择VM
- **适用场景**: 简单的命令执行、状态查询
- **回退机制**: VM离线时自动在本地执行

### 2. 并行任务 (parallel)

- **执行策略**: 主节点和VM同时执行
- **适用场景**: 需要双节点确认的任务、数据收集
- **结果处理**: 自动合并两个节点的执行结果

### 3. VM专用任务 (vm-only)

- **执行策略**: 必须在VM执行
- **适用场景**: Moltbook监控、本地资源访问
- **失败处理**: VM离线时任务失败，不回退

## 子代理并发

系统支持在双节点上并发运行多个子代理：

```bash
# 启动多个子代理
for i in {1..3}; do
    ./scripts/task-dispatcher.sh subagent vm "echo '并发任务 $i'"
done

# 本地也启动子代理
for i in {1..2}; do
    ./scripts/task-dispatcher.sh subagent local "echo '本地任务 $i'"
done
```

## 监控与日志

### 查看日志

```bash
# 主节点日志
tail -f /var/log/linlin/task-dispatcher.log

# VM执行器日志
ssh -i /tmp/linlin_cloud_key -p 4444 root@user-virtual-machine \
    "tail -f /var/log/linlin/task-executor.log"
```

### 启动心跳服务

```bash
# 在VM上启动心跳服务（后台运行）
ssh -i /tmp/linlin_cloud_key -p 4444 root@user-virtual-machine \
    "nohup /opt/linlin/task-executor.sh heartbeat 30 > /dev/null 2>&1 &"

# 查看心跳
ls -la /var/run/linlin/heartbeat/
```

### 健康检查

```bash
# 检查VM执行器状态
ssh -i /tmp/linlin_cloud_key -p 4444 root@user-virtual-machine \
    "/opt/linlin/task-executor.sh health"

# 检查主节点状态
./scripts/task-dispatcher.sh status
```

## 故障排查

### VM连接失败

```bash
# 测试SSH连接
ssh -v -i /tmp/linlin_cloud_key -p 4444 root@user-virtual-machine "echo test"

# 检查端口监听
netstat -tlnp | grep 4444

# 检查防火墙
iptables -L | grep 4444
```

### 任务执行失败

```bash
# 查看详细日志
grep "ERROR" /var/log/linlin/task-dispatcher.log

# 手动测试任务执行
./scripts/task-dispatcher.sh dispatch lightweight test-task 'date' 2>&1
```

### 权限问题

```bash
# 修复文件权限
chmod +x scripts/task-dispatcher.sh /opt/linlin/task-executor.sh

# 修复目录权限
chown -R root:root /var/run/linlin /var/log/linlin /opt/linlin
```

## 高级配置

### 环境变量

```bash
# 调试模式
export DEBUG=1

# 自定义日志路径
export LOG_FILE=/custom/path/dispatcher.log

# 自定义任务目录
export TASK_QUEUE_DIR=/custom/tasks
export TASK_RESULTS_DIR=/custom/results

# VM执行器启用主节点上报
export REPORT_TO_MASTER=1
```

### 集成到工作流

```bash
# 在脚本中调用
#!/bin/bash
source ./scripts/task-dispatcher.sh dispatch vm-only monitor-$(date +%s) '' ./scripts/system-monitor.sh
```

## API 参考

### 任务结果格式

```json
{
  "task_id": "task-001",
  "timestamp": 1707643200,
  "status": "success",
  "node": "vm",
  "exit_code": 0,
  "output": "命令输出内容..."
}
```

### 并行任务结果格式

```json
{
  "task_id": "task-002",
  "timestamp": 1707643200,
  "status": "success",
  "type": "parallel",
  "results": {
    "local": {
      "exit_code": 0,
      "output": "本地输出..."
    },
    "vm": {
      "exit_code": 0,
      "output": "VM输出...",
      "online": true
    }
  }
}
```

## 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2025-02-11 | 1.0 | 初始版本，支持三种任务类型和子代理并发 |

## 联系方式

如有问题，请检查日志文件或联系系统管理员。
