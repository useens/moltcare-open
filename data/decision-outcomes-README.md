# 决策效果追踪系统

## 文件说明

| 文件 | 用途 |
|------|------|
| `data/decision-engine.jsonl` | 决策引擎原始运行记录 |
| `data/decision-outcomes.jsonl` | 决策效果追踪记录（效果验证闭环） |

## 数据格式

### decision-outcomes.jsonl

每条记录包含以下字段：

```json
{
  "decision_id": "debt-20260219-001",      // 决策唯一标识
  "task_type": "debt_processing",          // 任务类型
  "risk_level": "L5_HIGH",                 // 风险等级
  "expected_result": "预期执行结果描述",    // 预期结果
  "actual_result": "实际执行结果描述",      // 实际结果
  "execution_time_ms": 5230.5,             // 执行耗时(毫秒)
  "timestamp": "2026-02-19T13:30:00",      // ISO格式时间戳
  "success": true,                         // 是否成功
  "quality_score": 8,                      // 质量评分 1-10
  "notes": "执行正常"                       // 备注
}
```

## 任务类型

- `technical_design` - 技术设计
- `architecture_change` - 架构变更
- `security_response` - 安全响应
- `performance_opt` - 性能优化
- `debt_processing` - 学习债务处理
- `system_maintenance` - 系统维护
- `evolution_task` - 进化任务

## 风险等级

- `L1_IMMEDIATE` - 立即执行
- `L2_ROUTINE` - 常规执行
- `L3_STANDARD` - 标准执行
- `L4_SIGNIFICANT` - 重要变更
- `L5_HIGH` - 高风险
- `L6_CRITICAL` - 关键决策

## 使用方法

### 生成效果报告

```bash
python3 scripts/autonomous-decision-engine.py --report
```

### 查询特定决策

```bash
python3 scripts/autonomous-decision-engine.py --query-id debt-20260219-001
```

### 按类型查询

```bash
python3 scripts/autonomous-decision-engine.py --query-type debt_processing
```

### 查看最近30天的报告

```bash
python3 scripts/autonomous-decision-engine.py --report --report-days 30
```

## 质量评分算法

质量分计算 (1-10分)：
- 基础分：5分
- 执行成功：+2分
- 专家置信度加权：最高+2分
- 超进化完成率：最高+2分

## 创建时间

2026-02-19 | 决策效果追踪系统 v1.0
