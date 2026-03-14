# MoltCare + OpenClaw 快速开始

> 🚀 **5分钟上手指南** | 从安装到首次对话

---

## 📋 目录

1. [核心概念](#核心概念)
2. [OpenClaw 已自动提供的功能](#openclaw-已自动提供的功能)
3. [首次配置（3步）](#首次配置3步)
4. [验证配置](#验证配置)
5. [下一步](#下一步)

---

## 核心概念

### MoltCare 是什么？

MoltCare 是**配置模板框架**，提供：
- ✅ Agent 行为原则（SOUL.md）
- ✅ 操作手册（AGENTS.md）
- ✅ 用户画像模板（USER.md）

### OpenClaw 是什么？

OpenClaw 是**运行时环境**，提供：
- ✅ Project Context 自动加载
- ✅ 工具调用系统（read/edit/exec/memory_search 等）
- ✅ 会话管理

### 关键理解

```
MoltCare 配置需要 Agent 主动遵循
OpenClaw 不会自动强制执行
```

---

## OpenClaw 已自动提供的功能

| 功能 | 说明 | 你需要做什么 |
|------|------|--------------|
| **Project Context** | 自动加载 SOUL.md/USER.md | 什么都不做 ✅ |
| **memory_search** | 检索 MEMORY.md 和 memory/*.md | 调用工具即可 ✅ |
| **工具透明** | 自动展示工具调用记录 | 天然满足 ✅ |
| **sessions_spawn** | 创建子 Agent（可选） | 按需使用 ⚠️ |

---

## 首次配置（3步）

### Step 1: 应用 Foundation Pack

```bash
# 克隆并应用
moltcare apply foundation

# 或指定路径
moltcare apply foundation --path ./my-project
```

### Step 2: 填写 USER.md（5分钟）

```markdown
# 打开 USER.md，填写以下内容：

## 👤 基本信息
- **称呼**: 你的名字
- **角色**: 全栈工程师 / 产品经理 / ...
- **技术水平**: 初级 / 进阶 / 专家

## 💬 沟通偏好
- **详细程度**: 适中
- **语气**: 友好
- **技术深度**: 实践

## ⚙️ 系统偏好
- **自动化**: L1-L3自动，L4-L5确认
```

### Step 3: 创建 memory 目录

```bash
mkdir -p memory
```

---

## 验证配置

### 测试 1：检查自动加载
```
开始新对话，Agent 应该：
✅ 自动知道你的称呼
✅ 自动使用你偏好的语气
```

### 测试 2：检查触发词
```
你说："记住这个：学习 Kubernetes"
Agent 应该：
✅ 回复"已记录到学习债务"
✅ 更新 memory/learning-debt.md
```

### 测试 3：检查记忆检索
```
你说："我之前让你记住什么？"
Agent 应该：
✅ 使用 memory_search 检索
✅ 返回之前的学习债务
```

---

## 下一步

### 深入理解机制
→ [机制说明](INTEGRATION_MECHANISM.md)

### 遇到问题？
→ [故障排除](INTEGRATION_TROUBLESHOOTING.md)

### 完整功能列表
→ [原完整指南](INTEGRATION.md)

---

*快速开始指南*
*预计阅读时间：5分钟*
*预计配置时间：5分钟*
