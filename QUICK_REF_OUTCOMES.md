# 决策效果追踪系统 - 快速参考

## ⚡ 快速命令

### 测试功能
```bash
# 测试追踪功能（写入一条测试记录）
python3 /root/.openclaw/workspace/scripts/autonomous-decision-engine.py --test-outcomes
```

### 查看数据
```bash
# 查看统计和分析
python3 /root/.openclaw/workspace/view-outcomes.py

# 查看原始JSON数据
cat /root/.openclaw/workspace/data/decision-outcomes.jsonl

# 查看带行号
cat -n /root/.openclaw/workspace/data/decision-outcomes.jsonl
```

### 运行决策
```bash
# 运行完整决策周期（会自动追踪）
python3 /root/.openclaw/workspace/scripts/autonomous-decision-engine.py --cycle

# 仅检查学习债务
python3 /root/.openclaw/workspace/scripts/autonomous-decision-engine.py --debt-check

# 仅检查系统问题
python3 /root/.openclaw/workspace/scripts/autonomous-decision-engine.py --system-check
```

---

## 📊 数据字段解释

| 字段 | 类型 | 说明 |
|------|------|------|
| decision_id | string | 决策唯一标识符 |
| task_type | string | 任务类型 (system_maintenance/debt_processing等) |
| risk_level | string | 风险等级 (L1-L6) |
| expected_result | string | 预期结果描述 |
| actual_result | string | 实际执行结果 |
| execution_time_ms | float | 执行耗时(毫秒) |
| timestamp | string | ISO格式时间戳 |
| success | boolean | 是否成功 |
| quality_score | int | 质量评分 1-10 |
| notes | string | 备注信息 |

---

## 🎯 质量评分计算

基础分: 5

加分项:
- 执行成功: +2
- 专家置信度高: 0-2 (基于平均置信度)
- 超进化完成率: 0-2 (基于完成阶段比例)

最终: 1-10 (限制范围)

---

## 📍 文件位置

| 文件 | 路径 |
|------|------|
| 主脚本 | `/root/.openclaw/workspace/scripts/autonomous-decision-engine.py` |
| 数据文件 | `/root/.openclaw/workspace/data/decision-outcomes.jsonl` |
| 测试脚本 | `/root/.openclaw/workspace/test-outcome-tracking.py` |
| 查看工具 | `/root/.openclaw/workspace/view-outcomes.py` |
| 部署报告 | `/root/.openclaw/workspace/reports/decision-outcome-deployment-summary.md` |
| 本文档 | `/root/.openclaw/workspace/QUICK_REF_OUTCOMES.md` |

---

## 📈 验证清单

- ✅ 数据文件存在
- ✅ 写入功能正常
- ✅ 读取功能正常
- ✅ 统计分析正确
- ✅ 质量评分正常
- ✅ 无Python错误

---

**更新**: 2026-02-19 13:35
**状态**: ✅ 生产就绪
