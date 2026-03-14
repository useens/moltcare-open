# MoltCare + OpenClaw 故障排除

> 🔧 **问题解决指南** | 常见问题及解决方案

---

## 📋 目录

1. [触发词问题](#触发词问题)
2. [记忆系统问题](#记忆系统问题)
3. [多专家系统问题](#多专家系统问题)
4. [常见误解澄清](#常见误解澄清)

---

## 触发词问题

### 问题1：触发词不生效

**症状**：说"记住这个"但 Agent 没有记录

**检查清单**：
1. Agent 是否在回复前检查触发词？
2. 触发词匹配是否准确（包含空格、标点）？
3. 是否区分大小写？

**解决方案**：
```python
# 添加日志调试
print(f"检查触发词：{user_message}")
for keyword in triggers:
    if keyword in user_message:
        print(f"命中：{keyword}")

# 确保匹配逻辑正确
if "记住这个" in user_message:  # 不是 "记住"
    add_learning_debt(content)
```

### 问题2：触发词误触发

**症状**：正常对话中被误判为触发词

**解决方案**：
```python
# 使用更精确的匹配
triggers = {
    "记住这个：": {...},  # 带冒号更精确
    "记住这个 ": {...},   # 或带空格
}

# 或使用正则
def check_triggers(msg):
    if re.search(r"记住这个[：:]", msg):
        return True
```

---

## 记忆系统问题

### 问题1：记忆检索不到

**症状**：memory_search 返回空结果

**检查清单**：
1. 文件是否在正确位置？
2. 文件是否已保存？
3. memory_search 查询词是否准确？

**解决方案**：
```bash
# 检查文件位置
ls -la memory/
ls -la MEMORY.md

# 尝试不同查询词
memory_search("用户偏好")
memory_search("preference")
memory_search("偏好")
```

### 问题2：记忆内容混乱

**症状**：检索结果包含无关内容

**解决方案**：
```markdown
# 在记忆文件中使用明确的标记
### [PREFERENCE] 用户偏好
### [TASK] 待办任务
### [LEARNING] 学习债务
```

---

## 多专家系统问题

### 问题1：多专家输出混乱

**症状**：专家观点混杂，无法区分

**解决方案**：
```markdown
# 使用固定格式分隔
<details>
<summary>🧠 多专家讨论记录</summary>

### 🔍 研究员观点
- 关键事实：...

### 🧠 架构师观点
- 设计影响：...

### 👑 队长综合决策
**结论**：...
</details>
```

### 问题2：子代理成本过高

**症状**：sessions_spawn 导致响应缓慢

**解决方案**：
- 减少子代理数量（≤3个）
- 改用单 Agent 模拟（sequential）
- 仅对复杂决策使用子代理

---

## 常见误解澄清

### 误解1："触发词会自动执行"

**现实**：
- ❌ OpenClaw 没有 pre_message hook
- ✅ 需要 Agent 主动检查消息内容
- ✅ 每次回复前手动调用检查函数

### 误解2："多专家是真正的并行"

**现实**：
- ❌ 默认是单 Agent 模拟（sequential）
- ✅ 如需真正并行，使用 sessions_spawn（高成本）
- ✅ 大多数场景单 Agent 模拟已足够

### 误解3："有心跳守护进程"

**现实**：
- ❌ OpenClaw 没有后台守护进程
- ✅ HEARTBEAT.md 是提示词约定
- ✅ 需要外部 cron 或用户手动触发

### 误解4："记忆会自动管理"

**现实**：
- ❌ Signal 评估需要 Agent 判断
- ❌ 记忆写入需要 Agent 调用 write/edit
- ✅ memory_search 是自动的，但存储是手动的

---

## 获取帮助

### 诊断命令

```bash
# 检查模板版本
moltcare show foundation

# 检查文件结构
ls -la
ls memory/

# 检查配置
moltcare config get
```

### 相关文档

- [快速开始](INTEGRATION_QUICKSTART.md) - 基础配置
- [机制说明](INTEGRATION_MECHANISM.md) - 深入理解
- [完整指南](INTEGRATION.md) - 所有功能

---

*故障排除指南*
*按图索骥，快速定位问题*
