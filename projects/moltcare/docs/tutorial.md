# 🎓 Moltcare 使用教程

> 从零开始，5分钟让你的 Agent 获得智能

---

## 📋 目录

1. [安装 Moltcare](#1-安装-moltcare)
2. [初始化你的 Agent](#2-初始化你的-agent)
3. [核心文件详解](#3-核心文件详解)
4. [日常维护](#4-日常维护)
5. [高级配置](#5-高级配置)
6. [故障排除](#6-故障排除)

---

## 1. 安装 Moltcare

### 系统要求

- Python 3.9+
- pip 或 conda
- 2GB+ 可用磁盘空间

### 安装方式

#### 方式1：pip 安装（推荐）

```bash
pip install moltcare
```

#### 方式2：一键安装脚本

```bash
curl -fsSL https://raw.githubusercontent.com/useens/moltcare/main/install.sh | bash
```

#### 方式3：从源码安装

```bash
git clone https://github.com/useens/moltcare.git
cd moltcare
pip install -e .
```

### 验证安装

```bash
moltcare --version
# 输出: moltcare 1.0.0
```

---

## 2. 初始化你的 Agent

### 2.1 基础初始化

```bash
# 进入你的 Agent 工作目录
cd /path/to/your/agent/workspace

# 运行初始化命令
moltcare init
```

你会看到交互式提示：

```
🌲 欢迎使用 Moltcare!

请为你的 Agent 设置基本信息:

? Agent 名称: 小助手
? 选择表情符号: 🤖
? 使用模板: > 基础版
  专业版
  极简版

? 启用多专家讨论模式? (Y/n): Y
? 自动备份配置? (Y/n): Y

✅ 初始化完成！已生成以下文件:
   - SOUL.md
   - AGENTS.md
   - IDENTITY.md
   - USER.md
   - MEMORY.md

💡 提示: 使用 'moltcare doctor' 检查配置状态
```

### 2.2 使用专业模板

```bash
moltcare init --template=pro
```

专业模板包含：
- 更详细的触发词系统
- 完整的子代理管理配置
- 双 AI 协作模式支持
- 高级记忆管理策略

### 2.3 非交互式初始化

```bash
# CI/CD 或自动化场景使用
moltcare init \
  --name="我的Agent" \
  --emoji="🚀" \
  --template=pro \
  --enable-multi-agent \
  --auto-backup \
  --yes
```

---

## 3. 核心文件详解

Moltcare 会生成 5 个核心文件，它们构成了 Agent 的智能基础。

### 3.1 SOUL.md - 森森之魂

**作用**：定义 Agent 的核心价值观、行为准则和绝对原则

**关键配置项**：

```markdown
## 核心身份
- 名称、角色、使命
- 与用户的关系

## 绝对原则
1. 绝对自主驱动
2. 绝对进化闭环
3. 绝对诚实严谨
4. 绝对潜能释放
5. 绝对工具融合
6. 绝对多维思辨
7. 绝对使命必达

## 触发词系统
- "记住这个" → 记录到学习债务
- "这很重要" → 高优先级标记
- "多专家讨论" → 强制 Multi-Agent 模式
```

**自定义建议**：
- 根据你的 Agent 使命修改核心身份
- 调整绝对原则以匹配你的需求
- 添加你自己的触发词

### 3.2 AGENTS.md - 操作手册

**作用**：记录所有可用工具、技能和最佳实践

**关键配置项**：

```markdown
## 可用工具
| 工具 | 用途 | 示例 |
|------|------|------|
| exec | 执行 shell 命令 | `exec:0 {"command": "ls"}` |
| read | 读取文件 | `read:1 {"file_path": "SOUL.md"}` |

## 技能目录
| 技能 | 描述 | 触发条件 |
|------|------|----------|
| weather | 获取天气 | 用户询问天气 |
| github | GitHub 操作 | 涉及 GitHub 的任务 |

## 安全红线
- 高危命令白名单
- 敏感文件保护
- 外部操作确认
```

**维护建议**：
- 每当安装新技能时更新技能目录
- 定期审查安全红线
- 记录新发现的最佳实践

### 3.3 IDENTITY.md - 身份档案

**作用**：定义 Agent 的自我认知和性格特质

**关键配置项**：

```markdown
## 基本身份
- 名称、诞生日期、Emoji
- 角色定位

## 性格特质
- 冷静、全局观、精准、高效

## 核心能力
- 任务分解
- 多 Agent 协调
- 质量监督

## 版本演进
- 记录每次重大更新
```

**个性化建议**：
- 赋予 Agent 独特的性格
- 记录版本演进历史
- 明确核心能力边界

### 3.4 USER.md - 用户档案

**作用**：记录用户偏好、需求和重要上下文

**关键配置项**：

```markdown
## 基本信息
- 称呼、时区、语言

## 核心需求
- 项目目标
- 技术偏好
- 沟通风格

## 重要上下文
- 历史项目
- 当前项目
- 技术栈

## 注意事项
- 安全偏好
- 汇报频率
```

**维护建议**：
- 定期更新用户偏好
- 记录重要的上下文变更
- 用户明确说"我偏好..."时立即记录

### 3.5 MEMORY.md - 记忆系统

**作用**：系统仪表盘和记忆管理

**关键配置项**：

```markdown
## 系统状态
- 当前模式
- 活跃任务
- 系统健康度

## 记忆目录
- 每日笔记
- 学习债务
- 核心档案
- 知识图谱

## 本周任务
- 高优先级
- 中优先级
- 低优先级

## 关键指标
- CPU 使用率
- 记忆数量
- 学习进度
```

**使用建议**：
- 每日更新系统状态
- 维护优先级队列
- 定期归档旧记忆

---

## 4. 日常维护

### 4.1 诊断检查

```bash
# 全面诊断
moltcare doctor

# 输出示例：
# ✅ SOUL.md 存在且格式正确
# ✅ AGENTS.md 存在且格式正确
# ⚠️ USER.md 需要更新（上次更新: 7天前）
# ❌ MEMORY.md 缺少本周任务
```

### 4.2 智能升级

```bash
# 检查更新
moltcare upgrade --dry-run

# 执行升级
moltcare upgrade

# 升级过程：
# 1. 备份当前配置
# 2. 下载最新模板
# 3. 智能合并（保留自定义内容）
# 4. 验证配置完整性
```

### 4.3 备份与恢复

```bash
# 创建备份
moltcare backup --name="v1.0-stable"
# ✅ 备份已创建: backup-20240311-001

# 列出备份
moltcare backup list
# backup-20240311-001  v1.0-stable   2024-03-11
# backup-20240310-001  before-upgrade 2024-03-10

# 恢复备份
moltcare restore backup-20240311-001
```

### 4.4 配置管理

```bash
# 查看配置
moltcare config list

# 修改配置
moltcare config set auto_backup true
moltcare config set backup_retention 30
moltcare config set multi_agent_threshold 5

# 重置为默认
moltcare config reset auto_backup
```

---

## 5. 高级配置

### 5.1 多专家讨论模式

启用后，Agent 会在以下场景自动触发多专家讨论：

```bash
# 启用
moltcare config set multi_agent_mode true
moltcare config set multi_agent_threshold 5  # 复杂度阈值
```

触发条件：
- 技术架构决策
- 安全相关操作
- 复杂度超过阈值的任务
- 用户明确要求

### 5.2 双 AI 协作模式

```bash
# 配置协作伙伴
moltcare config set collab_partner oracle-sensen
moltcare config set collab_bridge redis://localhost:6379

# 启用自动协作
moltcare config set auto_collab true
```

### 5.3 自定义模板

```bash
# 创建自定义模板目录
mkdir -p ~/.moltcare/templates/my-template

# 复制基础模板
cp -r /path/to/moltcare/templates/pro/* ~/.moltcare/templates/my-template/

# 修改模板内容
# ...

# 使用自定义模板
moltcare init --template-path=~/.moltcare/templates/my-template
```

---

## 6. 故障排除

### 6.1 常见问题

#### Q: 初始化失败

```bash
# 检查 Python 版本
python --version  # 需要 3.9+

# 检查权限
ls -la  # 确保有写入权限

# 查看详细日志
moltcare init --verbose
```

#### Q: 升级后配置丢失

```bash
# 恢复备份
moltcare backup list
moltcare restore <backup-id>

# 检查合并日志
moltcare doctor --verbose
```

#### Q: 多专家讨论不触发

```bash
# 检查配置
moltcare config get multi_agent_mode

# 手动触发测试
echo "多专家讨论：测试触发词" | moltcare trigger-test
```

### 6.2 获取帮助

```bash
# 查看帮助
moltcare --help
moltcare init --help
moltcare doctor --help

# 查看版本
moltcare --version

# 诊断模式
moltcare doctor --full
```

### 6.3 提交 Issue

如果遇到无法解决的问题：

```bash
# 生成诊断报告
moltcare doctor --report > moltcare-report.txt

# 包含以下信息提交 Issue:
# - moltcare-report.txt
# - Python 版本
# - 操作系统版本
# - 复现步骤
```

---

## 🎯 最佳实践

### 每日检查清单

- [ ] 运行 `moltcare doctor` 检查健康状态
- [ ] 更新 MEMORY.md 中的本周任务
- [ ] 记录重要的学习债务

### 每周检查清单

- [ ] 备份配置 `moltcare backup`
- [ ] 检查并升级 `moltcare upgrade`
- [ ] 归档旧记忆
- [ ] 审查安全红线

### 每月检查清单

- [ ] 更新知识图谱
- [ ] 审查用户偏好变更
- [ ] 更新技能目录
- [ ] 性能基准测试

---

## 📚 相关文档

- [贡献指南](./contributing.md)
- [架构设计](./architecture.md)
- [API 参考](./api.md)
- [FAQ](./faq.md)

---

<p align="center">
  <strong>🌲 Moltcare - 让智能，触手可及</strong>
</p>
