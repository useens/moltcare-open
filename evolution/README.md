# Hyper-Evolution Engine v2.0

自我进化、智能化改写自身的自动化系统。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行一次完整进化评估
python -m hyper-evolution evaluate

# 查看状态
python -m hyper-evolution status

# 手动执行策略
python -m hyper-evolution execute --strategy cost_optimization
```

## 架构概览

- `core/` - 核心引擎、事件总线、状态管理
- `collectors/` - 数据收集（性能、行为、系统、外部）
- `decider/` - 决策引擎、触发条件、策略选择
- `executor/` - 安全执行、沙箱、回滚
- `strategies/` - 具体进化策略库
- `sandbox/` - 隔离测试环境
- `config/` - 配置文件
- `tests/` - 测试用例

## 设计原则

- 安全第一：所有变更必须先沙箱验证
- 渐进部署：10% → 50% → 100%
- 自动回滚：失败立即恢复
- 可解释性：每次进化都有完整日志

## 当前状态

Phase 1 进行中：数据收集器开发完成。
