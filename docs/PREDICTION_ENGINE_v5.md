# 林林v5.0 预判引擎集成文档

## 概述

预判引擎v5.0是林林系统的核心智能组件，能够在用户开口前预测需求并主动提供帮助。

## 核心组件

### 1. 预判引擎核心集成 (`core/prediction_integration.py`)

主要功能：
- **时间模式学习**: 分析用户24小时活跃模式
- **上下文关联**: 关联日历、邮件、项目预测需求
- **A/B测试优化**: 动态调整预测策略
- **实时预判触发**: 对话后自动分析并预测

### 2. 实时预判触发器 (`scripts/realtime_predictor.py`)

触发类型：
- 对话后触发
- 定时触发（默认30分钟）
- 上下文变化触发
- 事件驱动触发（日历/邮件/项目）

### 3. 主流程集成 (`core/main_flow_integration.py`)

集成方案：
- 继承模式
- 组合模式
- 装饰器模式

### 4. 准确率报告 (`core/prediction_accuracy_report.py`)

报告内容：
- 整体准确率统计
- A/B测试结果分析
- 时间模式准确率
- 优化建议

## 快速开始

### 方案1: 新建项目使用预判引擎

```python
import asyncio
from core.main_flow_integration import PredictionEnabledMainFlow

async def main():
    # 创建启用预判的流程
    flow = PredictionEnabledMainFlow()
    await flow.initialize()
    
    # 处理消息（自动集成预判）
    result = await flow.process_message("帮我看看今天的邮件")
    
    # 输出包含预判建议
    print(f"响应: {result['response']}")
    if result['suggestions_before']:
        print(f"对话前建议: {result['suggestions_before']}")
    
    await flow.shutdown()

asyncio.run(main())
```

### 方案2: 集成到现有主流程

```python
# 在现有类中添加
from scripts.realtime_predictor import RealtimePredictor

class MyExistingFlow:
    async def __init__(self):
        # ... 原有初始化 ...
        
        # 初始化预判引擎
        self.predictor = RealtimePredictor()
        await self.predictor.start()
    
    async def process_message(self, message):
        # 1. 对话前检查建议
        suggestions = await self.predictor.prediction_integration.generate_proactive_suggestions()
        
        # 2. 处理消息
        response = await self._process_core(message)
        
        # 3. 对话后分析
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "content": message,
            "response": response
        }
        await self.predictor.on_conversation_end(conversation)
        
        return response
```

## 配置选项

### 预判引擎配置

```python
# 实时预判器配置
predictor.update_config(
    scheduled_interval_minutes=30,      # 定时检查间隔
    context_check_interval_minutes=5,   # 上下文检查间隔
    min_confidence_for_proactive=0.75   # 主动建议最小置信度
)

# 主流程预判配置
flow.update_config(
    auto_show_suggestions=True,         # 自动显示建议
    min_confidence_to_show=0.75,        # 显示建议的最小置信度
    max_suggestions_per_turn=2          # 每轮最大建议数
)
```

### A/B测试配置

预判引擎会自动将用户分配到不同测试组：
- **control**: 标准策略（阈值0.7）
- **treatment_a**: 激进策略（阈值0.6）
- **treatment_b**: 保守策略（阈值0.8）

系统自动收集数据并推荐最佳策略。

## 反馈收集

### 接受建议

```python
# 当用户接受建议时
flow.accept_suggestion(prediction_id)
```

### 拒绝建议

```python
# 当用户拒绝建议时
flow.reject_suggestion(prediction_id, actual_need="真实需求")
```

## 生成报告

### JSON格式报告

```python
from core.prediction_accuracy_report import generate_accuracy_report

# 生成最近30天的报告
report_path = generate_accuracy_report(days=30, output_format="json")
print(f"报告已保存: {report_path}")
```

### Markdown格式报告

```python
# 生成Markdown报告
report_path = generate_accuracy_report(days=30, output_format="markdown")
```

### 控制台汇总

```python
from core.prediction_accuracy_report import print_summary_report

# 打印汇总报告
print_summary_report(days=30)
```

## 数据文件

预判引擎会生成以下数据文件（在 `data/` 目录）：

- `time_patterns.json` - 学习时间模式
- `context_associations.json` - 上下文关联数据
- `ab_test_results.json` - A/B测试结果
- `prediction_feedback.json` - 预测反馈数据
- `dynamic_thresholds.json` - 动态阈值配置
- `reports/` - 准确率报告

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     林林v5.0 预判引擎                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  实时预判触发器   │◄───│  时间模式学习器   │              │
│  │  Realtime        │    │  TimePattern     │              │
│  │  Predictor       │    │  Learner         │              │
│  └────────┬─────────┘    └──────────────────┘              │
│           │                                                 │
│           ▼                                                 │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  预判引擎集成     │◄───│  上下文关联引擎   │              │
│  │  Prediction      │    │  ContextAssoc    │              │
│  │  Integration     │    │  Engine          │              │
│  └────────┬─────────┘    └──────────────────┘              │
│           │                                                 │
│           ▼                                                 │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  A/B测试优化器   │───►│  准确率报告生成   │              │
│  │  ABTest          │    │  AccuracyReport  │              │
│  │  Optimizer       │    │                  │              │
│  └──────────────────┘    └──────────────────┘              │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  触发方式:                                                    │
│  • 对话后分析    • 定时检查    • 上下文变化    • 事件驱动      │
└─────────────────────────────────────────────────────────────┘
```

## API参考

### PredictionIntegration

```python
class PredictionIntegration:
    async def analyze_conversation(conversation, context) -> List[PredictionResult]
    async def generate_proactive_suggestions(context) -> List[PredictionResult]
    def record_feedback(prediction_id, was_accurate, actual_need, was_accepted)
    def get_prediction_report() -> Dict
```

### RealtimePredictor

```python
class RealtimePredictor:
    async def start()
    async def stop()
    async def on_conversation_end(conversation, context) -> List[PredictionResult]
    async def on_calendar_event(event) -> List[PredictionResult]
    async def on_email_arrival(emails) -> List[PredictionResult]
    async def on_project_update(project) -> List[PredictionResult]
    def record_feedback(prediction_id, was_accurate, actual_need, was_accepted)
    def get_stats() -> Dict
```

### PredictionEnabledMainFlow

```python
class PredictionEnabledMainFlow:
    async def initialize()
    async def shutdown()
    async def process_message(message, user_id, context) -> Dict
    async def before_conversation() -> Optional[List[PredictionResult]]
    async def after_conversation(conversation, context) -> List[PredictionResult]
    def accept_suggestion(prediction_id)
    def reject_suggestion(prediction_id, actual_need)
```

## 最佳实践

1. **及时收集反馈**: 用户接受或拒绝建议时立即记录反馈
2. **定期检查报告**: 每周查看准确率报告，调整策略
3. **合理设置阈值**: 根据用户接受度动态调整置信度阈值
4. **避免过度打扰**: 保持冷却时间，避免频繁建议
5. **持续训练**: 积累的对话数据会不断提升预测准确率

## 故障排除

### 预判引擎不工作

1. 检查是否正确初始化：`await flow.initialize()`
2. 检查预判是否启用：`flow._prediction_enabled`
3. 查看统计信息：`flow.get_prediction_stats()`

### 准确率过低

1. 提高置信度阈值：`flow.update_config(min_confidence_to_show=0.8)`
2. 检查反馈数据是否正确记录
3. 查看A/B测试报告，切换到更好的策略

### 建议过于频繁

1. 增加冷却时间
2. 提高最小置信度阈值
3. 减少每轮最大建议数

## 更新日志

### v5.0 (2026-02-11)
- 初始版本发布
- 实现时间模式学习
- 实现上下文关联
- 实现A/B测试优化
- 实现实时预判触发
- 实现准确率报告生成
