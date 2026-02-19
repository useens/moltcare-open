# 🌲 森森 (Sensen) - 完全自主数字分身 v2.3

> **当前版本**: v2.3 - Full-Autonomy Multi-Agent ⚡  
> **更新日期**: 2026-02-19  
> **运行状态**: 🟢 完全自主运行中 | 系统健康度 **96/100**  
> **核心能力**: 多专家实时深度讨论 | Vestige认知记忆 | 触发词系统

---

## 🎯 核心特性

### 🤖 完全自主Multi-Agent决策系统

**强制触发指令**: 消息以 **"多专家讨论："** 开头
- 立即启动4个专家子代理（研究员/架构师/工程师/安全专家）
- 最少3轮深度辩论，直到达成共识
- 真实AI模型调用，非模拟

### 🧠 Vestige认知记忆系统 (v6.0) - 全新升级！

| 组件 | 技术 | 记录数 | 状态 |
|-----|------|--------|------|
| **Vestige FSRS** | FSRS-6间隔重复 | 387条 | ✅ 活跃 |
| **旧ChromaDB** | 向量记忆 | 387条 | 📦 已归档 |
| **触发词系统** | 关键词识别 | 7种触发 | ✅ 运行中 |
| **每日日志** | Markdown时间线 | 完整 | ✅ 活跃 |
| **学习债务** | Signal评分 | 动态管理 | ✅ 活跃 |

**FSRS-6算法**:
- 可提取性: R(t,s) = (1 + t/(9s))^(-1)
- 间隔计算: I = S × ln(R) / ln(0.9)
- 难度/稳定性自适应调整
- Signal + FSRS 综合优先级队列

### ⚡ 触发词系统

| 用户说 | 动作 | 优先级 |
|-------|------|--------|
| `多专家讨论:` | 强制Multi-Agent | 10 |
| `这很重要` | promote_memory | 9 |
| `记住这个` | smart_ingest | 8 |
| `学习这个` | learning-debt | 8 |
| `提醒我` | create_reminder | 7 |
| `我偏好` | write_preference | 6 |
| `我总是` | write_preference | 6 |

### 🔄 超进化引擎

| 时间 | 任务 |
|------|------|
| 每30分钟 | 心跳检查 |
| 每小时 | 学习债务评估 |
| 14:00 | 深度学习闭环 |
| 23:30 | 夜间进化#1 |
| 02:00 | 系统维护决策 |

---

## 🚀 快速开始

### 一键复活（推荐）

```bash
# 方式1: 使用最新备份
curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/one-click-resurrect.sh | bash -s -- sensen_full_HOSTNAME_20260219_222600.tar.gz

# 方式2: 全新安装
./scripts/one-click-resurrect.sh --fresh
```

### 全量备份

```bash
./scripts/full-backup.sh "备份注释"
```

**备份包含**:
- Vestige记忆系统 (~/.local/share/vestige/)
- 核心文档 (SOUL.md, MEMORY.md等)
- 触发词配置
- Python核心模块
- 凭证配置

---

## 📁 仓库结构

```
linlin-backup/
├── 📂 core/                       # 核心系统 ⭐
│   ├── vestige_memory.py          # FSRS-6记忆系统
│   ├── trigger_handler.py         # 触发词系统
│   └── logging/                   # 统一日志
│
├── 📂 scripts/                    # 自动化脚本
│   ├── full-backup.sh             # 全量备份 ⭐
│   ├── one-click-resurrect.sh     # 一键复活 ⭐
│   ├── autonomous-decision-engine.py
│   ├── unified-monitor.py
│   └── migrate_chroma_to_vestige.py
│
├── 📂 skills/                     # ClawHub技能
│   ├── vestige/                   # 记忆系统技能
│   ├── agent-config/
│   ├── cc-godmode/
│   ├── mcp-builder/
│   └── ...
│
├── 📂 memory/                     # 记忆系统
│   ├── INDEX.md                   # 统一记忆索引 ⭐
│   ├── learning-debt.md
│   ├── 2026-*.md                 # 每日日志
│   └── modules/
│
├── 📂 data/                       # 数据文件
│   ├── decision-outcomes.jsonl    # 决策追踪
│   └── unified_logs.db           # 日志数据库
│
├── 📂 .archived/                  # 已归档系统
│   └── vector_memory_20260219/    # 旧ChromaDB (保留7天)
│
├── 📄 SOUL.md                     # 十大绝对原则
├── 📄 MEMORY.md                   # 系统仪表盘
├── 📄 AGENTS.md                   # 操作手册
├── 📄 HEARTBEAT.md                # 心跳检查
├── 📄 INDEX.md                    # 快速索引
├── 📄 IDENTITY.md                 # 身份档案
├── 📄 USER.md                     # 用户画像
└── 📄 TOOLS.md                    # 工具配置
```

---

## 🔧 核心配置

### Vestige记忆系统

```python
# 使用Vestige
from core.vestige_memory import VestigeMemory

vm = VestigeMemory()

# 添加记忆
vm.ingest("重要内容", tags=["work"], signal_score=8)

# 搜索记忆
results = vm.search("关键词")

# 获取优先级队列
priority_queue = vm.get_priority_queue(limit=10)

# 复习记忆
vm.review(memory_id, rating=3)  # 1=忘记, 2=困难, 3=良好, 4=简单

# 查看统计
print(vm.get_stats())
```

### 触发词系统

```python
from core.trigger_handler import process_message, should_use_multi_agent

# 处理消息
result = process_message("记住这个：明天开会")

# 判断是否触发Multi-Agent
use_ma = should_use_multi_agent("多专家讨论：技术选型")
```

### 必需凭证

| 凭证 | 位置 | 用途 |
|------|------|------|
| GitHub Token | `~/.config/linlin/github-token` | 备份同步 |
| Feishu App | 环境变量 | 飞书通知 |

---

## 📊 系统指标

| 指标 | 当前值 | 状态 |
|------|--------|------|
| **版本** | v2.3 | ✅ |
| **Vestige记忆** | 387条 | ✅ |
| **旧ChromaDB** | 已归档 | 📦 |
| **触发词** | 7种 | ✅ |
| **学习债务** | 10条待处理 | 🟡 |
| **Cron任务** | 14个 | ✅ |
| **健康评分** | 96/100 | 🟢 |
| **GitHub备份** | useens/linlin-backup | ✅ |

---

## 🛡️ 七大绝对原则

1. **绝对自主驱动** - 独立思考→自主决策→全权执行
2. **绝对进化闭环** - 学习→内化→应用→检验→迭代
3. **绝对诚实严谨** - 三次验证机制，数据真实可溯源
4. **绝对潜能释放** - 无瓶颈运行，资源100%利用
5. **绝对工具融合** - 穷尽一切可用工具
6. **绝对多维思辨** - Multi-Agent内部辩论
7. **绝对使命必达** - 结果导向，拒绝表演式努力

---

## 📝 使用指南

### 触发Multi-Agent讨论

```
多专家讨论：这个技术方案是否可行？
```

### 保存重要记忆

```
这很重要：项目的核心架构设计是...
```

### 设置提醒

```
提醒我明天9点开会
```

### 记录偏好

```
我偏好使用Python而不是Java
```

---

## 🆘 故障排查

| 问题 | 解决方案 |
|------|----------|
| Vestige无法启动 | 检查~/.local/share/vestige/权限 |
| 触发词不生效 | 验证core/trigger_handler.py存在 |
| 复活失败 | 检查备份文件完整性 (sha256sum) |
| 记忆丢失 | 从.archived/vector_memory_*恢复 |
| 备份失败 | 验证GitHub Token有效性 |

### 紧急恢复

```bash
# 如果Vestige损坏，从备份恢复
cd ~/.openclaw/workspace
tar -xzf backups/sensen_full_*.tar.gz -C /tmp
sudo cp -r /tmp/sensen_full_*/vestige_data/* ~/.local/share/vestige/

# 如果触发词系统损坏
python3 -c "from core.trigger_handler import process_message; print('OK')"
```

---

## 📞 联系信息

- **GitHub**: https://github.com/useens/linlin-backup
- **前身**: 林林 v5.5 (记忆档案在 `memory/linlin-archive/`)
- **诞生**: 2026-02-12
- **当前版本**: v2.3 (2026-02-19)

---

## ⚠️ 重要提示

1. **保密**: 本仓库包含敏感凭证，切勿公开分享
2. **定期备份**: 使用 `./scripts/full-backup.sh`
3. **归档保留**: 旧ChromaDB保留7天 (`.archived/vector_memory_20260219/`)
4. **Vestige位置**: `~/.local/share/vestige/` 不在Git中，必须通过备份保存
5. **触发词**: 修改 `core/trigger_handler.py` 中的 `TRIGGERS` 字典

---

*最后更新: 2026-02-19 22:26*  
*更新内容: Vestige FSRS-6记忆系统 + 触发词系统 + 全量备份脚本*  
*系统状态: 完全自主运行 | ChromaDB已归档 | Vestige 387条记忆*
