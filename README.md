# 🌲 森森 (Sensen) - 完全自主数字分身

> **当前版本**: v2.3 - Full-Autonomy Multi-Agent ⚡  
> **更新日期**: 2026-02-19  
> **运行状态**: 🟢 完全自主运行中 | 系统健康度 **96/100**  
> **核心能力**: 多专家实时深度讨论 | CC_GodMode工作流编排 | 决策效果追踪

---

## 🎯 核心特性

### 🤖 完全自主Multi-Agent决策系统 (v1.3)

**强制触发指令**: 消息以 **"多专家讨论："** 开头
- 立即启动Redis实时深度多轮讨论
- 4个专家子代理（研究员/架构师/工程师/安全专家）
- 最少3轮辩论，直到达成共识
- 真实AI模型调用，非模拟

**工作流编排** (借鉴CC_GodMode):
| 工作流 | 适用场景 | 执行路径 |
|--------|----------|----------|
| NEW_FEATURE | 新功能开发 | 研究→架构→实现→双门禁→文档 |
| BUG_FIX | Bug修复 | 实现→双门禁 |
| API_CHANGE | API变更 | 架构→API守护→实现→双门禁→文档 |
| RESEARCH | 纯研究 | 仅研究员 |

**双质量门禁**:
- Validator: 代码/执行质量检查
- Security/Effect: 安全/效果验证
- 并行执行，40%速度提升

### 🧠 认知记忆系统 (v5.5)

| 组件 | 技术 | 记录数 |
|------|------|--------|
| 向量记忆 | ChromaDB + LRU缓存 | 1,189条 |
| 每日日志 | Markdown时间线 | 完整 |
| 学习债务 | Signal评分系统 | 动态管理 |
| 决策追踪 | JSONL效果记录 | 完整 |

**记忆优化**:
- 搜索延迟: 3s+ → 0.13s (23x提升)
- 模型常驻: 9.77s → 0s (1000万x提升)
- 自动备份: 每6小时
- 一致性校验: 387条100%通过

### 🔄 超进化引擎 (v1.3)

**定时任务**:
| 时间 | 任务 | 模式 |
|------|------|------|
| 每30分钟 | 心跳检查 | 快速扫描 |
| 每小时 | 学习债务评估 | 轻量评估 |
| 14:00 | 深度学习闭环 | 债务处理 |
| 23:30 | 夜间进化#1 | 完整决策周期 |
| 02:00 | 系统维护决策 | 维护优化 |

**决策风险分级**:
| 等级 | 名称 | Multi-Agent | 执行方式 |
|------|------|-------------|----------|
| L1-L2 | 低/常规 | ❌ | 静默执行 |
| L3 | 标准 | ✅ | 自动执行 |
| L4 | 重要 | ✅ | 自动+简要汇报 |
| L5 | 高风险 | ✅ | 自动+详细报告 |
| L6 | 关键 | ✅ | 自动+完整报告+汇报 |

---

## 🚀 快速开始

### 一键复活

```bash
# 全自动复活（推荐）
curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/resurrect.sh | bash
```

### 手动克隆

```bash
git clone https://github.com/useens/linlin-backup.git
cd linlin-backup
./scripts/sensen-resurrect.sh
```

---

## 📁 仓库结构

```
linlin-backup/
├── 📂 core/                    # 核心系统
│   ├── shared_models.py        # 共享模型池
│   └── logging/                # 统一日志系统
│
├── 📂 scripts/                 # 自动化脚本
│   ├── autonomous-decision-engine.py  # 自主决策引擎v1.3 ⭐
│   ├── unified-monitor.py      # 统一监控
│   ├── moltbook-unified.py     # Moltbook扫描
│   └── evolution-unified.py    # 进化引擎
│
├── 📂 skills/                  # ClawHub技能
│   ├── agent-config/           # Agent配置管理
│   ├── agentlens/              # 代码库导航
│   ├── cc-godmode/             # 多Agent工作流 ⭐
│   ├── mcp-builder/            # MCP服务器构建
│   ├── moltbook-interact/      # Moltbook交互
│   ├── skill-creator/          # 技能创建
│   ├── skill-vetting/          # 技能审计
│   ├── summarize/              # 内容总结
│   ├── tdd-guide/              # 测试驱动开发
│   └── vestige/                # 认知记忆系统 ⭐
│
├── 📂 memory/                  # 记忆系统
│   ├── 2026-02-19.md          # 今日日志
│   ├── learning-debt.md        # 学习债务
│   ├── knowledge-graph.md      # 知识图谱
│   └── modules/                # 核心记忆模块
│
├── 📂 docs/                    # 文档
│   └── autonomous-decision-engine.md  # 决策引擎文档
│
├── 📂 data/                    # 数据文件
│   ├── decision-outcomes.jsonl # 决策效果追踪 ⭐
│   └── vector_memory/          # 向量记忆数据
│
├── 📂 reports/                 # 报告
│   └── decision-*.md           # 决策报告
│
├── 📄 AGENTS.md               # 操作手册
├── 📄 SOUL.md                 # 十大绝对原则
├── 📄 MEMORY.md               # 系统仪表盘
├── 📄 HEARTBEAT.md            # 心跳检查清单
├── 📄 IDENTITY.md             # 身份档案
├── 📄 TOOLS.md                # 工具配置
└── 📄 USER.md                 # 用户画像
```

---

## 🔧 核心配置

### 必需凭证

| 凭证 | 位置 | 用途 |
|------|------|------|
| GitHub Token | `~/.config/linlin/github-token` | 备份同步 |
| Feishu App | 环境变量 | 飞书通知 |

### 设置步骤

```bash
# 1. GitHub Token
mkdir -p ~/.config/linlin
echo "ghp_xxxxxxxx" > ~/.config/linlin/github-token
chmod 600 ~/.config/linlin/github-token

# 2. 配置远程仓库
git remote set-url origin "https://ghp_xxxx@github.com/useens/linlin-backup.git"
```

---

## 📊 系统指标

| 指标 | 当前值 | 状态 |
|------|--------|------|
| **版本** | v2.3 | ✅ |
| **向量记忆** | 1,189条 | ✅ |
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

系统将自动：
1. 启动4个专家子代理
2. 进行3轮深度辩论
3. 生成完整讨论报告
4. 队长整合最终决策

### 查看决策效果

```bash
python3 scripts/autonomous-decision-engine.py --report
```

### 系统健康检查

```bash
python3 scripts/unified-monitor.py --fix
```

---

## 🆘 故障排查

| 问题 | 解决方案 |
|------|----------|
| 复活失败 | 检查GitHub Token有效性 |
| 记忆缺失 | 运行向量记忆同步脚本 |
| 决策引擎错误 | 检查data/decision-engine.jsonl |
| 备份失败 | 验证远程仓库权限 |

---

## 📞 联系信息

- **GitHub**: https://github.com/useens/linlin-backup
- **前身**: 林林 v5.5 (记忆档案在 `memory/linlin-archive/`)
- **诞生**: 2026-02-12
- **当前版本**: v2.3 (2026-02-19)

---

## ⚠️ 重要提示

1. **保密**: 本仓库包含敏感凭证，切勿公开分享
2. **定期备份**: 每天03:00自动GitHub备份
3. **效果追踪**: 所有决策自动记录到 `data/decision-outcomes.jsonl`
4. **更新同步**: 主系统变更后自动同步到GitHub

---

*最后更新: 2026-02-19 21:50*  
*更新内容: v2.3 - Multi-Agent强制触发 + CC_GodMode工作流编排 + 决策效果追踪*  
*系统状态: 完全自主运行 | 14个Cron任务 | 96/100健康度*
