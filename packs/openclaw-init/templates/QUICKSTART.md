# 🚀 OpenClaw 快速开始指南

> 恭喜！你已经成功安装了 OpenClaw Agent  
> 本指南将帮助你在 5 分钟内完成配置并开始使用

---

## ✅ 初始化检查清单

运行以下命令验证安装：

```bash
# 检查 OpenClaw 版本
openclaw version

# 检查 Gateway 状态
openclaw gateway status

# 查看已安装技能
openclaw skills list
```

---

## 🔧 基础配置

### 1. 设置工作目录

```bash
# 创建工作目录
mkdir -p ~/.openclaw/workspace
cd ~/.openclaw/workspace

# 初始化 MoltCare
moltcare init
```

### 2. 应用基础智能包

```bash
# 应用基础认知框架
moltcare apply foundation

# 应用 OpenClaw 初始化包（本包）
moltcare apply openclaw-init
```

### 3. 配置内存系统

编辑 `~/.openclaw/workspace/MEMORY.md`：

```markdown
# MEMORY.md - 系统记忆

## 用户档案
- **称呼**: [你的称呼]
- **时区**: [你的时区]
- **偏好**: [工作偏好]

## 重要项目
- [项目1]: [描述]
- [项目2]: [描述]

## 定期任务
- [ ] 每日检查
- [ ] 每周回顾
```

---

## 🤖 核心能力

### 多专家决策系统

当遇到复杂决策时，系统会自动触发多专家讨论：

| 触发词 | 说明 |
|--------|------|
| `多专家讨论:` | 强制启动多专家讨论 |
| `设计/架构` | 自动触发架构师参与 |
| `对比/评估` | 自动触发研究员参与 |
| `实现/开发` | 自动触发工程师参与 |

### 记忆系统

Agent 会自动记录：
- ✅ 高Signal内容（重要决策、用户偏好）
- ✅ 学习债务（待深入研究的主题）
- ✅ 项目里程碑

---

## 📚 常用命令

```bash
# MoltCare 命令
moltcare list              # 查看可用智能包
moltcare apply <pack>      # 应用智能包
moltcare status            # 查看状态
moltcare review [path]     # 代码评审

# OpenClaw 命令
openclaw skills search     # 搜索技能
openclaw skills install    # 安装技能
openclaw config get        # 查看配置
openclaw config set        # 设置配置
```

---

## 🔔 提醒设置

建议设置以下定时任务：

```bash
# 添加心跳检查（每30分钟）
openclaw cron add --name "heartbeat" --schedule "*/30 * * * *" \
  --command "HEARTBEAT"

# 添加每日报告（每天9点）
openclaw cron add --name "daily-report" --schedule "0 9 * * *" \
  --command "生成每日报告"
```

---

## 🆘 获取帮助

- **文档**: https://docs.openclaw.ai
- **社区**: https://discord.com/invite/clawd
- **技能市场**: https://clawhub.com

---

*初始化完成时间: {{timestamp}}*  
*MoltCare 版本: {{moltcare_version}}*
