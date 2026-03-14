# Daily Log Template - 每日日志

> 📅 **YYYY-MM-DD 工作日志** | Signal 6-7 的日常记录

---

## 📊 今日概览

### 基本信息
| 字段 | 值 |
|------|-----|
| **日期** | {{YYYY-MM-DD}} |
| **星期** | {{DAY_OF_WEEK}} |
| **工作日类型** | {{WORK_DAY_TYPE}} |

### 今日统计
| 指标 | 数值 |
|------|------|
| 会话数 | {{COUNT}} |
| 完成任务 | {{COMPLETED}}/{{TOTAL}} |
| 学习债务进展 | {{PROGRESS}} |
| 错误数 | {{ERRORS}} |

---

## ✅ 已完成任务

### 高优先级
- [x] {{TASK_DESCRIPTION}} (耗时: {{DURATION}})
  - 结果: {{RESULT}}
  - 备注: {{NOTES}}

### 中优先级
- [x] {{TASK_DESCRIPTION}} (耗时: {{DURATION}})

### 低优先级
- [x] {{TASK_DESCRIPTION}} (耗时: {{DURATION}})

---

## ⏳ 进行中任务

| 任务 | 进度 | 预计完成 | 阻塞项 |
|------|------|----------|--------|
| {{TASK}} | {{PROGRESS}}% | {{DATE}} | {{BLOCKER}} |

---

## 🆕 新发现

### 新技能
| 技能 | 来源 | 熟练度 | 练习次数 |
|------|------|--------|----------|
| {{SKILL}} | {{SOURCE}} | ⭐⭐⭐ | {{COUNT}} |

### 新知识
- {{KNOWLEDGE}} (来源: {{SOURCE}})

### 新工具
| 工具 | 用途 | 评价 |
|------|------|------|
| {{TOOL}} | {{PURPOSE}} | {{RATING}} |

---

## ⚠️ 问题与阻碍

| 问题 | 严重程度 | 解决方案 | 状态 |
|------|----------|----------|------|
| {{ISSUE}} | {{SEVERITY}} | {{SOLUTION}} | {{STATUS}} |

---

## 📝 重要交互

### 关键对话
**时间**: {{TIME}}
**主题**: {{TOPIC}}
**用户反馈**: {{FEEDBACK}}
**Signal**: {{SIGNAL}}

### 决策记录
| 决策 | 背景 | 结果 |
|------|------|------|
| {{DECISION}} | {{CONTEXT}} | {{OUTCOME}} |

### 用户偏好更新
- {{DATE}}: 用户偏好 {{PREFERENCE}} = {{VALUE}}

---

## 🔥 学习债务更新

### 新增
| 主题 | Signal | 来源 |
|------|--------|------|
| {{TOPIC}} | {{SIGNAL}} | {{SOURCE}} |

### 进展
| 主题 | 进度 | 预计完成 |
|------|------|----------|
| {{TOPIC}} | {{PROGRESS}}% | {{DATE}} |

### 完成
- ✅ {{TOPIC}} (完成时间: {{DATE}})

---

## ❌ 今日错误

| 错误 | 根因 | 改进措施 |
|------|------|----------|
| {{ERROR}} | {{CAUSE}} | {{IMPROVEMENT}} |

---

## 🎯 明日计划

### 高优先级
- [ ] {{TASK}}

### 中优先级
- [ ] {{TASK}}

### 提醒
- ⏰ {{REMINDER}}

---

## 💭 反思与总结

### 今日亮点
{{HIGHLIGHT}}

### 待改进
{{IMPROVEMENT}}

### 明日期待
{{EXPECTATION}}

---

## 📎 附件

### 相关文件
- {{FILE_PATH}}

### 相关链接
- {{LINK}}

---

*每日结束时由 Agent 自动生成或更新*
*Signal 6-7 的内容自动归档到每日日志*
*每周回顾时整合到 MEMORY.md*

## 使用方法

### 创建新日志
```bash
# 复制模板
cp DAILY_TEMPLATE.md memory/2026-03-14.md

# 或使用 Agent
Agent: 创建今日日志
```

### 日志归档
```
memory/
├── 2026-03-14.md  ← 今日日志
├── 2026-03-13.md  ← 昨日日志
├── 2026-03-12.md  ← 更早日志
└── ...
```

### 检索历史
```python
# 使用 memory_search
memory_search("2026-03-14 完成的任务")
memory_search("学习债务进展")
```
