# 林林v5.0 预判引擎 v0.1 文档

## 概述

预判引擎是林林v5.0的核心组件，目标是在用户开口前预测需求并主动满足。通过分析用户行为模式、历史对话和当前上下文，引擎能够生成个性化的主动建议。

## 核心功能

### 1. 用户行为模式分析

#### 活跃时段分析
- **功能**: 分析用户一天中的活跃时间段
- **实现**: `analyze_active_hours()`
- **输出**: 每小时活跃度统计、高峰时段、安静时段

#### 请求模式识别
- **功能**: 识别高频请求类型和时机
- **实现**: `identify_request_patterns()`
- **输出**: 请求类型分布、周期性模式

#### 工作节奏检测
- **功能**: 检测深度工作时段和休息时段
- **实现**: `detect_work_rhythm()`
- **输出**: 深度工作时段、高频时段、休息时段

### 2. 需求预测模型

#### 时间预测
```python
predictions = engine.predict_by_time(current_time)
```
- 基于历史同期数据预测
- 特殊时间点规则（如早晨简报）
- 置信度评分

#### 上下文预测
```python
context = {
    "recent_emails": [...],
    "upcoming_events": [...],
    "workload": {...}
}
predictions = engine.predict_by_context(context)
```
- 基于邮件、日程、任务负载预测

#### 历史模式预测
```python
predictions = engine.predict_by_history(lookback_days=7)
```
- 周期性模式识别（每日/每周）
- 特殊日期规则（周一/周五）

### 3. 主动建议生成

```python
suggestions = engine.generate_suggestions(context)
```

**过滤规则:**
- 置信度 ≥ 0.7
- 4小时内不重复相同建议
- 最多返回3个建议

**个性化:**
- 根据沟通风格调整语气（简洁/详细/随意）
- 根据优先级分类（高/中/低）

### 4. 学习反馈循环

```python
# 记录反馈
engine.record_feedback(prediction_id, was_accurate, actual_need)

# 获取学习报告
report = engine.get_learning_report()
```

**反馈类型:**
- 准确命中: 强化该模式
- 误判: 分析原因并调整阈值

## 文件结构

```
workspace/
├── core/
│   └── prediction_engine.py      # 预判引擎核心
├── scripts/
│   └── learn-user-pattern.py     # 用户模式学习脚本
├── data/
│   └── user_pattern.json         # 用户模式数据库
└── docs/
    └── prediction-engine.md      # 本文档
```

## 使用方法

### 基础使用

```python
from core.prediction_engine import PredictionEngine

# 初始化引擎
engine = PredictionEngine(data_dir="data")

# 分析历史对话
conversations = [...]  # 历史对话列表
engine.analyze_active_hours(conversations)
engine.identify_request_patterns(conversations)

# 生成建议
context = {"recent_emails": [...]}
suggestions = engine.generate_suggestions(context)

# 保存模式
engine.save_user_pattern()
```

### 运行学习脚本

```bash
# 完整学习周期
python scripts/learn-user-pattern.py --full-cycle

# 仅从最近7天学习
python scripts/learn-user-pattern.py --days 7

# 包含反馈数据
python scripts/learn-user-pattern.py --feedback data/feedback.json
```

### 用户模式数据库结构

```json
{
  "version": "0.1",
  "behavior_patterns": {
    "hourly_activity": {...},
    "day_of_week": {...},
    "request_types": {...},
    "work_rhythm": {...}
  },
  "preferences": {
    "communication_style": "concise|detailed|casual",
    "notification_preference": "aggressive|moderate|minimal",
    "preferred_topics": [...],
    "avoided_topics": [...]
  },
  "prediction_rules": [...],
  "feedback_history": [...],
  "prediction_accuracy": {
    "total_predictions": 0,
    "correct_predictions": 0,
    "accuracy_rate": 0.0
  }
}
```

## 预测准确率目标

- **v0.1目标**: 70%+
- **测量方法**: `prediction_accuracy.accuracy_rate`
- **优化策略**:
  1. 持续收集用户反馈
  2. 误判时自动调整阈值
  3. 定期运行学习脚本

## 扩展计划

### v0.2 规划
- [ ] 集成更多数据源（邮件、日历API）
- [ ] 引入机器学习模型
- [ ] 支持更复杂的周期性模式
- [ ] 多用户模式支持

### v0.3 规划
- [ ] 实时预测能力
- [ ] 自然语言生成建议
- [ ] A/B测试框架
- [ ] 预测解释性增强

## 注意事项

1. **隐私保护**: 用户模式数据存储在本地，不对外传输
2. **性能**: 学习脚本建议在低峰时段运行
3. **迭代**: v0.1为轻量级实现，快速迭代优先

## 调试与监控

```python
# 查看学习报告
learner = UserPatternLearner()
report = learner.generate_learning_report()
print(json.dumps(report, indent=2))
```

## 贡献与反馈

如有问题或建议，请记录在 `data/feedback.json` 中:

```json
[
  {
    "prediction_id": "pred_001",
    "was_accurate": false,
    "actual_need": "search",
    "timestamp": "2026-02-11T10:00:00"
  }
]
```
