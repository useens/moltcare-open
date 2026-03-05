# 🤖 Nanobot Command Center - 完整使用手册

## 概述

现在你有10个小弟(NB01-NB10)可用：
- **NB01-NB05**: Step 3.5 Flash (快速响应组)
- **NB06-NB10**: DeepSeek V3.2 (深度推理组)

大部分任务(约67-75%)会自动分配给小弟处理，复杂决策由你自己处理。

## 快速开始

### 1. 启动完整系统
```bash
cd /root/.openclaw/workspace
./scripts/cc-p0.sh start
```

### 2. 提交任务 (自动路由)
```bash
# 让系统自动决定交给谁
./scripts/delegate "测试所有节点的连接状态"

# 输出:
# 🤖 交给小弟处理 (step)
# ✅ 任务已提交: task_xxx -> NB01
```

### 3. 查看状态
```bash
./scripts/cc-p0.sh status
```

## 智能委托系统

### 自动路由规则

| 任务类型 | 示例 | 处理方式 |
|---------|------|---------|
| **数据收集** | "收集10个网站标题" | 给小弟 |
| **代码执行** | "运行测试脚本" | 给小弟 |
| **内容生成** | "生成周报模板" | 给小弟 |
| **批处理** | "处理100条数据" | 给小弟 |
| **决策判断** | "选择哪种架构" | 自己处理 |
| **策略规划** | "设计优化方案" | 自己处理 |
| **深度分析** | "为什么这个更好" | 自己处理 |

### 使用方式

#### 1. 自动路由 (推荐)
```bash
./scripts/delegate "你的任务内容"
# 系统自动决定交给小弟还是自己处理
```

#### 2. 指定节点
```bash
./scripts/delegate "任务内容" --to NB01
# 强制交给NB01处理
```

#### 3. 广播所有节点
```bash
./scripts/delegate "任务内容" --broadcast
# 分发给所有10个节点并行处理
```

#### 4. 强制自己处理
```bash
./scripts/delegate "任务内容" --self
# 强制自己处理，触发Multi-Agent深度思考
```

## 系统架构

```
用户请求
    │
    ▼
[任务路由器] ──分析任务复杂度──┐
    │                          │
    ├─简单任务(75%)──┐        │
    │                ▼        │
    │         [智能调度器]    │
    │                │        │
    │                ▼        │
    │         [任务队列]      │
    │                │        │
    │                ▼        │
    │         [10个小弟]      │
    │         NB01-NB10       │
    │                          │
    └─复杂任务(25%)───────────┘
                 │
                 ▼
         [你 - Multi-Agent]
         深度思考处理
```

## 高级用法

### 查看任务队列
```bash
python3 scripts/nb_relay_v2.py queue

# 输出:
# 📋 待处理任务: 5
#   task_xxx: [2] 测试节点连接... -> NB01
#   task_xxx: [1] 收集数据... -> NB02
```

### 手动处理队列
```bash
# 处理10个队列中的任务
./scripts/cc-p0.sh process 10
```

### 查看系统统计
```bash
python3 scripts/nb_relay_v2.py stats

# 输出:
# 📊 系统统计
# 队列状态:
#   pending: 3
#   completed: 15
# 节点状态:
#   NB01: step, 成功率100%, 评分1.00
#   ...
```

### 直接控制节点
```bash
# 直接发送消息到NB01
python3 scripts/nb-relay.py send NB01 "消息内容"

# 广播到所有节点
python3 scripts/nb-relay.py broadcast "消息内容"

# 与NB01对话
python3 scripts/nb-relay.py chat NB01
```

### 飞书通知
```bash
# 节点完成任务通知
python3 scripts/feishu-sync.py high node.NB01 "节点NB01任务完成"

# 系统告警
python3 scripts/feishu-sync.py critical system "节点NB01离线"

# 测试所有级别
python3 scripts/feishu-sync.py test
```

## 实际应用场景

### 场景1: 日常监控
```bash
# 让10个小弟分工检查不同服务
./scripts/delegate "检查服务A状态" --to NB01
./scripts/delegate "检查服务B状态" --to NB02
# ...

# 或者广播检查所有
./scripts/delegate "检查所有服务健康状态" --broadcast
```

### 场景2: 数据收集
```bash
# 10个节点并行收集不同数据源
./scripts/delegate "收集网站A数据" --to NB01
./scripts/delegate "收集网站B数据" --to NB02
# ...

# 收集完成后自己分析
./scripts/delegate "分析收集到的数据，找出趋势" --self
```

### 场景3: 代码任务
```bash
# 小弟测试代码
./scripts/delegate "运行单元测试" --to NB06  # DeepSeek组

# 自己处理复杂bug
./scripts/delegate "分析这个难以定位的bug" --self
```

### 场景4: 决策任务
```bash
# 让小弟提供方案
./scripts/delegate "列出3种可能的解决方案" --broadcast

# 自己做出最终决策
./scripts/delegate "综合以上方案，决定采用哪种" --self
```

## 文件位置

### 核心组件
- `core/task_queue.py` - 任务队列系统
- `core/scheduler.py` - 智能调度器
- `core/auto_recovery.py` - 自动故障恢复
- `core/task_router.py` - 任务路由器
- `core/auto_delegation.py` - 自动委托执行

### 脚本
- `scripts/cc-p0.sh` - P0系统管理
- `scripts/delegate` - 智能委托命令
- `scripts/nb_relay_v2.py` - 增强版Bot Relay
- `scripts/feishu-sync.py` - 飞书同步

### 数据
- `data/task_queue.db` - 任务队列数据
- `data/node_profiles.db` - 节点画像数据

## 故障排除

### 检查节点状态
```bash
./scripts/nb-cluster.sh status
```

### 重启单个节点
```bash
./scripts/nb-cluster.sh restart 1  # 重启NB01
```

### 查看日志
```bash
tail -f logs/p0/nanobots.log
tail -f logs/p0/auto_recovery.log
tail -f logs/p0/queue_processor.log
```

### 队列卡住
```bash
# 手动处理队列
./scripts/cc-p0.sh process 5
```

## 性能指标

当前系统预期：
- **任务分配比例**: 75%给小弟，25%自己处理
- **任务成功率**: >95%
- **故障恢复时间**: <30秒
- **队列处理能力**: 每分钟100+任务

## 最佳实践

1. **简单重复任务** → 给小弟
2. **重要决策判断** → 自己处理
3. **批量数据处理** → 广播到所有小弟
4. **复杂分析任务** → 自己处理
5. **监控检查任务** → 分发给不同小弟

## 快捷命令汇总

```bash
# 查看帮助
./scripts/cc-help.sh

# 系统管理
./scripts/cc-p0.sh status      # 查看状态
./scripts/cc-p0.sh start       # 启动系统
./scripts/cc-p0.sh stop        # 停止系统

# 智能委托
./scripts/delegate "任务"                    # 自动路由
./scripts/delegate "任务" --to NB01          # 指定节点
./scripts/delegate "任务" --broadcast        # 广播
./scripts/delegate "任务" --self             # 自己处理

# 队列管理
./scripts/cc-p0.sh process 10    # 处理10个任务
python3 scripts/nb_relay_v2.py queue    # 查看队列
python3 scripts/nb_relay_v2.py stats    # 查看统计
```

---

**版本**: v2.0 (P0 + 智能委托)
**更新时间**: 2026-03-05
**10个小弟状态**: ✅ 全部在线
