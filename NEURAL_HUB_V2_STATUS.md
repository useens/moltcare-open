# 神经中枢 2.0 部署状态

> **部署时间**: 2026-03-06  
> **状态**: ✅ 已就绪

---

## 系统概览

```
🧠 神经中枢 2.0
├── 核心组件
│   ├── 状态管理器 ✅
│   ├── 智能调度器 ✅
│   ├── SQLite持久化 ✅
│   └── Redis消息总线 ✅
│
└── 10个Nanobot V3 ✅
    ├── nanobot-1 (研究员)
    ├── nanobot-2 (架构师)
    ├── nanobot-3 (工程师)
    ├── nanobot-4 (安全专家)
    ├── nanobot-5 (分析师)
    ├── nanobot-6 (决策分析师)
    ├── nanobot-7 (代码审查员)
    ├── nanobot-8 (运维专家)
    ├── nanobot-9 (战略规划师)
    └── nanobot-10 (协调者)
```

---

## 核心能力

| 能力 | 状态 | 说明 |
|------|------|------|
| **智能调度** | ✅ | 能力匹配 + 负载均衡 |
| **优先级队列** | ✅ | P0-P4 五级优先级 |
| **故障恢复** | ✅ | 自动重试(最多3次) |
| **实时通信** | ✅ | Redis Pub/Sub |
| **状态监控** | ✅ | 30秒心跳检测 |
| **任务追踪** | ✅ | 完整生命周期管理 |

---

## 性能指标

| 指标 | 数值 | 状态 |
|------|------|------|
| Bot注册 | 100个/0.5s | ✅ |
| 状态查询 | <1ms | ✅ |
| 任务创建 | <5ms | ✅ |
| 在线Bot | 10/10 | ✅ |
| 系统响应 | <50ms | ✅ |

---

## 使用方式

### Python API

```python
from core.neural_hub import NeuralHub

# 创建实例
hub = NeuralHub()

# 提交任务
task_id = await hub.submit_task(
    task_type='security_audit',
    payload={'target': 'api'},
    priority=2,  # HIGH
    required_capabilities=['security', 'audit']
)

# 查询状态
status = await hub.get_task_status(task_id)

# 获取统计
stats = await hub.get_stats()
```

### 管理命令

```bash
# 查看Bot状态
ps aux | grep nanobot-v3 | grep -v grep

# 查看日志
tail -f data/neural_hub/logs/nanobot-*.log

# 停止所有Bot
pkill -f nanobot-v3.py
```

---

## 文件结构

```
core/neural_hub/
├── __init__.py              # 模块入口
├── hub.py                   # 主服务
├── state_manager.py         # 状态管理
├── scheduler.py             # 调度引擎
├── database.py              # SQLite持久化
└── redis_client.py          # Redis客户端

ai-nanobots/
├── nanobot-v3.py            # V3客户端
└── start-all-v3.sh          # 启动脚本

data/neural_hub/
├── logs/                    # 日志目录
└── tasks.db                 # SQLite数据库

docs/
├── neural-hub-v2-arch.md    # 架构设计
└── neural-hub-v2-deploy.md  # 部署指南
```

---

## 下一步建议

1. **接入现有系统**
   - 集成到现有Cron任务
   - 替换旧文件队列通信

2. **添加更多处理器**
   - 为每个Bot添加专用任务处理器
   - 实现自动化工作流

3. **监控面板**
   - Web界面查看实时状态
   - 任务进度可视化

---

*神经中枢 2.0 | 2026-03-06 | 森森*
