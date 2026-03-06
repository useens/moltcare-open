# 神经中枢 2.0 部署指南

## 项目结构

```
/root/.openclaw/workspace/
├── core/neural_hub/              # 神经中枢核心
│   ├── __init__.py
│   ├── hub.py                    # 主服务
│   ├── state_manager.py          # 状态管理
│   ├── scheduler.py              # 调度引擎
│   ├── database.py               # SQLite持久化
│   └── redis_client.py           # Redis客户端 (支持降级模式)
├── ai-nanobots/
│   ├── nanobot-v3.py             # V3客户端
│   ├── start-all-v3.sh           # 启动脚本
│   └── stop-all-v3.sh            # 停止脚本
├── data/neural_hub/              # 数据目录
│   ├── logs/                     # 日志
│   └── tasks.db                  # SQLite数据库
└── docs/neural-hub-v2-arch.md    # 架构文档
```

## 运行模式

### 降级模式 (无需Redis)
系统默认以降级模式运行，核心功能完全可用：
- ✅ 状态管理
- ✅ 智能调度
- ✅ 任务队列
- ✅ SQLite持久化

### 完整模式 (需要Redis)
启用Redis后获得实时通信能力：
- ✅ 低延迟消息 (<50ms)
- ✅ 实时广播
- ✅ 心跳同步

## 快速启动 (降级模式)

```bash
cd /root/.openclaw/workspace
python3 tests/integration_test.py
```

## Python API 使用

```python
import asyncio
from core.neural_hub import NeuralHub, TaskPriority

async def main():
    hub = NeuralHub()
    await hub.start()
    
    # 提交任务
    task_id = await hub.submit_task(
        task_type='code_review',
        payload={'file': 'test.py'},
        priority=TaskPriority.HIGH,
        required_capabilities=['code_review']
    )
    
    # 查看状态
    status = await hub.get_task_status(task_id)
    print(f"任务状态: {status}")
    
    # 系统统计
    stats = await hub.get_stats()
    print(stats)

asyncio.run(main())
```

## 系统特性

| 特性 | 降级模式 | 完整模式 |
|------|----------|----------|
| 状态管理 | ✅ | ✅ |
| 智能调度 | ✅ | ✅ |
| 任务队列 | ✅ | ✅ |
| SQLite持久化 | ✅ | ✅ |
| 实时通信 | ❌ | ✅ |
| 消息广播 | ❌ | ✅ |

## 性能指标

- 注册100个Bot: <0.5s
- 查询状态: <1ms
- 任务创建: <5ms
- 智能分配: <10ms

## 测试状态

- [x] 单元测试: 7/7 通过
- [x] 集成测试: 6/6 通过
- [x] 性能测试: 全部达标
- [x] 系统测试: 10个Bot正常注册和调度

## 注意事项

1. Redis为可选组件，系统可在降级模式下完整运行
2. 所有核心功能(SQLite、调度器、状态管理)不依赖Redis
3. 如需启用Redis实时通信，配置redis_url即可
