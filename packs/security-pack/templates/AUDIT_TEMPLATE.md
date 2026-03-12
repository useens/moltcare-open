# 安全审计配置

> MoltCare security-pack 自动生成

## 🔧 工具配置

### Bandit 配置

```yaml
# .bandit.yml
# 安全扫描配置

skips:
  - B101  # assert_used
  - B311  # random

assert_used:
  skips: ['*_test.py', 'test_*.py']

severity_level: LOW
confidence_level: LOW

exclude_dirs:
  - tests
  - venv
  - .venv
  - __pycache__

# 自定义测试
plugins:
  - name: custom_sql_check
    path: ./bandit_plugins
```

### Safety 策略

```json
{
  "ignored_vulnerabilities": [],
  "severity_threshold": "medium",
  "auto_update": true,
  "notification_channels": ["email", "slack"]
}
```

## 📝 审计报告模板

```markdown
# 安全审计报告

**日期**: {{date}}
**审计范围**: {{scope}}
**审计人员**: {{auditor}}

## 执行摘要

- **风险等级**: 🔴 高 / 🟡 中 / 🟢 低
- **发现问题**: {{total_issues}}
- **已修复**: {{fixed_issues}}
- **待处理**: {{pending_issues}}

## 详细发现

### 🔴 高危问题

#### 问题 1: {{title}}
- **位置**: {{file}}:{{line}}
- **描述**: {{description}}
- **风险**: {{risk}}
- **修复建议**: {{recommendation}}
- **修复期限**: {{deadline}}

### 🟡 中危问题
...

### 🟢 低危问题
...

## 工具扫描结果

### Bandit
```
{{bandit_output}}
```

### Safety
```
{{safety_output}}
```

### Semgrep
```
{{semgrep_output}}
```

## 修复计划

| 问题 | 优先级 | 负责人 | 期限 | 状态 |
|------|--------|--------|------|------|
| #1 | P0 | {{owner}} | {{date}} | 待修复 |

## 附录

- [ ] 扫描日志
- [ ] 修复记录
- [ ] 复测结果
```

## 🔄 定期审计流程

### 每周
- [ ] 运行 bandit 扫描
- [ ] 检查 safety 报告
- [ ] 审查新提交的代码

### 每月
- [ ] 完整依赖审计
- [ ] 密钥轮换检查
- [ ] 访问权限审查

### 每季度
- [ ] 全面安全评估
- [ ] 渗透测试
- [ ] 更新安全策略
