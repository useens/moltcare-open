# 林林v5.0 预判引擎

## 简介

林林v5.0预判引擎是一个智能预测系统，能够在用户开口前预测需求并主动提供帮助。

## 快速开始

```python
import asyncio
from core.main_flow_integration import PredictionEnabledMainFlow

async def main():
    flow = PredictionEnabledMainFlow()
    await flow.initialize()
    
    # 处理消息（自动集成预判）
    result = await flow.process_message("帮我看看今天的邮件")
    print(result['response'])
    
    await flow.shutdown()

asyncio.run(main())
```

## 核心功能

1. **实时预判触发** - 每次对话后分析上下文并预测
2. **时间模式学习** - 分析用户24小时活跃模式
3. **上下文关联** - 关联日历/邮件/项目预测需求
4. **A/B测试优化** - 动态调整预测策略

## 文件结构

```
core/
  ├── prediction_integration.py      # 预判引擎核心
  ├── main_flow_integration.py       # 主流程集成
  └── prediction_accuracy_report.py  # 准确率报告

scripts/
  ├── realtime_predictor.py          # 实时预判触发器
  └── integrate_prediction.py        # 集成工具

config/
  └── prediction_engine_v5.json      # 配置文件

docs/
  └── PREDICTION_ENGINE_v5.md        # 详细文档

tests/
  └── test_prediction_engine_v5.py   # 测试脚本
```

## 运行测试

```bash
python3 tests/test_prediction_engine_v5.py
```

## 文档

- [详细集成文档](docs/PREDICTION_ENGINE_v5.md)
- [完成报告](COMPLETION_REPORT_PREDICTION_v5.md)

## 配置

编辑 `config/prediction_engine_v5.json` 来调整预判引擎行为。

## License

MIT
