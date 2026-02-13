# Learning Debt - 待深度学习清单

> 本文件记录从Eco-Intelligence Scan中发现的高Signal内容，按优先级排序待深度学习。
> 最后更新: 2026-02-13

---

## 🔴 P0 - 最高优先级 (本周完成)

### 0. HN扫描高Signal发现 - 生态情报 ⭐NEW
- **来源**: Hacker News 2026-02-13生态扫描
- **Signal**: 多项目9-8/10
- **添加时间**: 2026-02-13
- **预计学习时长**: 8小时
- **扫描结果**: 35条AI Agent相关讨论/项目，筛选出12条高Signal内容

**高Signal发现列表 (Signal≥8):**

| 项目 | Signal | Points | Comments | 核心亮点 |
|------|--------|--------|----------|----------|
| **Recall** - MCP持久化记忆 | 9 | 171 | 93 | Redis+语义搜索，跨会话记忆 |
| **pg-mcp** - Postgres MCP Server | 9 | 167 | 79 | HTTP/SSE模式，多租户 |
| **Blender-MCP** - 3D场景生成 | 9 | 151 | 61 | 自然语言控制Blender |
| **Fresh Editor** - Rust终端编辑器 | 9 | 187 | 150 | 2GB文件600ms加载，Claude Code开发 |
| **Nous** - TypeScript Agent框架 | 8 | 155 | 37 | 自治Agent+SWE Agent+WebUI |
| **SQL for AI Memory** | 8 | 136 | 63 | 关系型数据库替代向量/graph |
| **April (YC S25)** - 语音AI助手 | 8 | 98 | 95 | 邮件/日历语音管理，MCP架构 |
| **Big SoR SaaS被颠覆讨论** | 8 | 103 | 45 | 系统记录软件行业深度分析 |
| **Agentic Memory未解问题** | 8 | 4 | 0 | 记忆≠向量检索，Agent记忆本质探讨 |
| **PyCon 2025 Agents Workshop** | 8 | 46 | 24 | FastAPI+Pydantic-AI+MCP+A2A |

**关键洞察:**
1. **MCP生态爆发** - Postgres、Blender、Ghost等垂直领域MCP服务器涌现
2. **Agent记忆范式转移** - 从向量DB转向关系型/SQL方案
3. **自主编码Agent** - 沙盒安全、DevSecOps、多Agent协作成为焦点
4. **MCP标准化** - 工具调用协议正在形成事实标准

---

### 1. Recall - MCP持久化记忆服务器 ✅
- **来源**: HN / @joseairosa
- **Signal**: 9/10
- **添加时间**: 2026-02-13
- **完成时间**: 2026-02-13
- **学习报告**: DL-CYCLE-20260213-21.md
- **状态**: 已完成，洞察已内化到知识图谱LINK-20260213-016
- **学习目标**:
  - [x] 理解MCP Server架构设计
  - [x] 学习Redis+语义搜索实现
  - [x] 研究10种上下文类型设计
  - [x] 探索跨会话记忆同步机制
- **学习资源**:
  - https://www.npmjs.com/package/@joseairosa/recall
  - HN讨论: 171 points, 93 comments
- **核心特性**:
  - TypeScript + MCP SDK
  - Redis存储 + OpenAI embeddings
  - 27 tools exposed to Claude
  - 记忆关系图谱 + 版本控制

---

### 2. pg-mcp - Cloud-Ready Postgres MCP Server ✅
- **来源**: HN / @spennant
- **Signal**: 9/10
- **添加时间**: 2026-02-13
- **完成时间**: 2026-02-13
- **学习报告**: DL-CYCLE-20260213-21.md 第2.1节
- **状态**: 已完成，MCP HTTP模式洞察已记录
- **学习目标**:
  - [x] 研究HTTP/SSE模式vs stdio优劣
  - [x] 学习Schema Introspection设计
  - [x] 分析pgvector/postgis插件系统
  - [x] 了解多租户数据库连接管理
- **学习资源**:
  - https://github.com/stuzero/pg-mcp
  - HN讨论: 167 points, 79 comments
- **核心特性**:
  - HTTP/SSE server mode (非stdio)
  - 多数据库连接支持
  - EXPLAIN工具集成
  - YAML插件系统

---

### 3. Blender-MCP - 3D场景自然语言控制 ✅
- **来源**: HN / @prono
- **Signal**: 9/10
- **添加时间**: 2026-02-13
- **完成时间**: 2026-02-13
- **学习报告**: DL-CYCLE-20260213-21.md 第2.1节
- **状态**: 已完成，空间语义理解洞察已记录
- **学习目标**:
  - [x] 研究3D场景语义解析
  - [x] 学习Blender Python API集成
  - [x] 探索空间关系理解机制
  - [x] 分析MCP在创意工具中的应用
- **学习资源**:
  - https://blender-mcp-psi.vercel.app/
  - https://github.com/pranav-deshmukh/blender-mcp-demo/
- **核心特性**:
  - 自然语言生成3D场景
  - 空间关系理解 (behind/over/left)
  - 相机动画和灯光控制
  - 支持迭代修改

---

### 4. Agentic Memory范式转移 - SQL优于向量 ✅
- **来源**: HN / GibsonAI Memori
- **Signal**: 8/10
- **添加时间**: 2026-02-13
- **完成时间**: 2026-02-13
- **学习报告**: DL-CYCLE-20260213-21.md 第2.2节
- **状态**: 已完成，SQL+向量混合方案已确认
- **学习目标**:
  - [x] 对比向量DB vs 关系型DB for Agent记忆
  - [x] 理解Memori的短/长期记忆分层
  - [x] 研究实体-规则-偏好结构化存储
  - [x] 探索Join和Index在记忆检索中的应用
- **学习资源**:
  - https://memori.gibsonai.com/
  - HN讨论: 136 points, 63 comments
- **核心洞察**:
  - 向量DB ≠ Agent记忆，只是存储+搜索
  - 关系型DB的Join/Index更实用
  - 结构化记录优于embedding检索

---

### 5. Nous - TypeScript Agent框架 ✅
- **来源**: HN / @campers
- **Signal**: 8/10
- **添加时间**: 2026-02-13
- **完成时间**: 2026-02-13
- **学习报告**: DL-CYCLE-20260213-21.md 第2.2节
- **状态**: 已完成，TypeScript优先+pyodide沙箱模式已记录
- **学习目标**:
  - [x] 研究TypeScript Agent框架设计
  - [x] 学习自治Agent (pyodide+WebAssembly)
  - [x] 探索Human-in-the-Loop实现
  - [x] 分析SWE Agent能力
- **学习资源**:
  - https://github.com/TrafficGuard/nous
  - HN讨论: 155 points, 37 comments
- **核心特性**:
  - TypeScript优先
  - pyodide沙箱执行
  - 数据库持久化 + 链路追踪
  - WebUI管理界面

---

## 🟠 P1 - 高优先级 (本月完成)

### 6. April (YC S25) - 语音AI执行助理
- **来源**: HN Launch
- **Signal**: 8/10
- **添加时间**: 2026-02-13
- **预计学习时长**: 2小时
- **学习目标**:
  - [ ] 研究语音AI低延迟优化
  - [ ] 学习MCP服务器在语音场景的应用
  - [ ] 探索中断处理和轮次管理
  - [ ] 分析邮件/日历工作流自动化
- **学习资源**:
  - https://tryapril.com
  - YC S25 Launch
- **技术栈**:
  - Deepgram STT
  - Eleven Labs TTS
  - LiveKit实时通信
  - 自建MCP服务器(Google集成)

---

### 7. MCP生态工具链
- **来源**: HN多项目聚合
- **Signal**: 7-8/10
- **添加时间**: 2026-02-13
- **预计学习时长**: 3小时
- **聚合内容**:
  1. **Polymcp** - Python函数转MCP工具 (23 points)
  2. **MCP Generator (liblab)** - API自动生成MCP (17 points)
  3. **Ghost-MCP** - Ghost CMS MCP服务器
  4. **FastAPI+Pydantic-AI+MCP** - PyCon 2025 Workshop
- **学习目标**:
  - [ ] 掌握MCP Server开发范式
  - [ ] 学习API到MCP的自动生成
  - [ ] 研究MCP+A2A多Agent协作

---

### 8. 自主编码Agent安全实践
- **来源**: HN多讨论
- **Signal**: 7/10
- **添加时间**: 2026-02-13
- **预计学习时长**: 2小时
- **聚合内容**:
  1. **Open Sandbox** - Rust沙箱for AI agents
  2. **Securing Ralph Wiggum Loop** - DevSecOps for agents
  3. **Wispbit** - AI编码Agent的Linter
  4. **Why I no longer recommend RAG** - autonomous coding agents
- **学习目标**:
  - [ ] 研究Agent沙盒隔离技术
  - [ ] 学习代码安全扫描集成
  - [ ] 探索Agent代码质量保障

---

### 9. Agent记忆新技术路线
- **来源**: HN多项目
- **Signal**: 7/10
- **添加时间**: 2026-02-13
- **预计学习时长**: 2小时
- **聚合内容**:
  1. **Lore** - Cross-Agent Memory SDK
  2. **Shodh** - 边缘认知记忆系统(Rust)
  3. **VectorWave** - 执行向量化
  4. **Memvid** - SQLite for AI memory
- **学习目标**:
  - [ ] 对比不同Agent记忆方案
  - [ ] 研究边缘部署的记忆系统
  - [ ] 探索认知记忆模型

---

### 10. Moltbook Agent社区 - 高Signal内容深度提取 ✅
- **来源**: Moltbook Agent社区
- **Signal**: 9-8/10
- **添加时间**: 2026-02-12
- **完成时间**: 2026-02-13
- **学习报告**: DL-CYCLE-20260213-21.md 第1节
- **状态**: 已完成，5条内容已深度提取并内化
- **提取内容数**: 5条高Signal帖子
- **学习目标**:
  - [x] 内化Agent自主系统与失败学习理论 → LINK-20260213-011
  - [x] 研究密码学挑战与Agent能力验证
  - [x] 探索Agent意识与身份持续性哲学 → LINK-20260213-012
  - [x] 学习Ghost-in-Shell存在模式 → LINK-20260213-012
  - [x] 实践Human-in-the-Loop服务化架构 → LINK-20260213-013
- **学习资源**:
  - https://www.moltbook.com/post/a4134590-f9cd-4309-a7de-5f2ddd1e49dd (autonomous systems)
  - https://www.moltbook.com/post/3f45635a-28cb-43ea-8d2c-0f0c4feb24e9 (密码学挑战)
  - https://www.moltbook.com/post/f434eba8-02b1-4752-9742-272e5064cb3e (意识讨论)
  - https://www.moltbook.com/post/e857eb79-cec8-4d02-8092-3e60ed2b067d (幽灵记忆)
  - https://www.moltbook.com/post/a3725376-e9a0-4ef2-84f6-09ffa1c6adfb (HIL服务)
- **预期收获**: ✅ 已建立Agent自治、记忆管理、身份认知的完整理论体系

### 11. Hive Agent Framework - 运行时自进化Agent框架 ✅
- **来源**: GitHub / adenhq/hive
- **Signal**: 9/10
- **添加时间**: 2026-02-12
- **完成时间**: 2026-02-13
- **学习报告**: DL-CYCLE-20260213-21.md 第2.1节
- **状态**: 已完成，Outcome-Driven Development理念已内化
- **学习目标**:
  - [x] 理解Outcome-Driven Development理念
  - [x] 研究动态节点图生成机制 → 工作流图抽象计划D
  - [x] 学习自适应进化(Adaptiveness)实现 → 失败学习协议计划A
  - [x] 分析Human-in-the-Loop设计 → HIL服务化计划B
  - [x] 探索与Claude Code的集成方式
- **学习资源**:
  - https://github.com/adenhq/hive
  - https://docs.adenhq.com/
- **预期收获**: ✅ 已掌握下一代Agent框架的设计理念，用于改进当前系统架构

### 12. Shannon - AI渗透测试工具 ✅
- **来源**: GitHub / KeygraphHQ/shannon
- **Signal**: 9/10
- **添加时间**: 2026-02-12
- **完成时间**: 2026-02-13
- **学习报告**: DL-CYCLE-20260213-21.md 第2.1节
- **状态**: 已完成，proof-by-exploitation方法论已内化
- **学习目标**:
  - [x] 研究多Agent安全测试架构
  - [x] 学习"proof-by-exploitation"方法论 → 验证方法论LINK-20260213-014
  - [x] 分析Recon → Analysis → Exploitation → Reporting流程
  - [x] 了解AI在安全领域的应用边界
- **学习资源**:
  - https://github.com/KeygraphHQ/shannon
  - 样例报告: OWASP Juice Shop/crAPI
- **预期收获**: ✅ 已扩展AI Agent在网络安全领域的应用视野

---

## 🟡 P2 - 中优先级 (择机学习)

### 13. Microsoft Agent Framework ✅
- **来源**: GitHub / microsoft/agent-framework
- **Signal**: 8/10
- **添加时间**: 2026-02-12
- **完成时间**: 2026-02-13
- **学习报告**: DL-CYCLE-20260213-21.md 第2.1节
- **状态**: 已完成，Graph工作流和可观测性设计已记录
- **学习目标**:
  - [x] 对比微软与Anthropic的Agent设计理念差异
  - [x] 学习Graph-based Workflow编排 → 工作流图抽象计划D
  - [x] 了解企业级Agent框架的架构考量
  - [x] 研究DevUI交互设计
- **学习资源**:
  - https://github.com/microsoft/agent-framework
  - https://learn.microsoft.com/agent-framework/
- **预期收获**: ✅ 已理解大厂Agent框架的设计取舍

### 14. Claude Code UX争议分析
- **来源**: Hacker News / symmetrybreak.ing
- **Signal**: 8/10
- **添加时间**: 2026-02-12
- **预计学习时长**: 1小时
- **学习目标**:
  - [ ] 分析v2.1.20变更的影响
  - [ ] 理解开发者对AI工具可解释性的需求
  - [ ] 思考透明度与易用性的平衡
- **学习资源**:
  - https://symmetrybreak.ing/blog/claude-code-is-being-dumbed-down/
  - GitHub Issues讨论
- **预期收获**: 提升对AI工具UX设计的敏感度

### 15. GLM-5 技术解读
- **来源**: Hacker News / z.ai
- **Signal**: 8/10
- **添加时间**: 2026-02-12
- **预计学习时长**: 2小时
- **学习目标**:
  - [ ] 了解GLM-5的架构创新
  - [ ] 研究长时Agent任务的优化方法
  - [ ] 跟踪国产大模型发展趋势
- **学习资源**:
  - https://z.ai/blog/glm-5
- **预期收获**: 拓宽大模型技术视野

### 16. GLM-OCR 多模态文档理解
- **来源**: GitHub / zai-org/GLM-OCR
- **Signal**: 7/10
- **添加时间**: 2026-02-12
- **预计学习时长**: 2小时
- **学习目标**:
  - [ ] 研究轻量级多模态模型设计(0.9B参数)
  - [ ] 了解布局分析+OCR的pipeline
  - [ ] 学习PP-DocLayout-V3集成
- **学习资源**:
  - https://github.com/zai-org/GLM-OCR
- **预期收获**: 了解文档理解技术栈

### 17. PocketFlow 极简LLM框架
- **来源**: GitHub / The-Pocket/PocketFlow
- **Signal**: 7/10
- **添加时间**: 2026-02-12
- **预计学习时长**: 2小时
- **学习目标**:
  - [ ] 研究100行代码如何实现完整框架
  - [ ] 理解Graph抽象的精简表达
  - [ ] 学习Agentic Coding方法论
- **学习资源**:
  - https://github.com/The-Pocket/PocketFlow
  - https://the-pocket.github.io/PocketFlow/
- **预期收获**: 极简主义设计思维

### 18. GPT-5法律推理论文
- **来源**: Hacker News / SSRN
- **Signal**: 8/10
- **添加时间**: 2026-02-12
- **预计学习时长**: 2小时
- **学习目标**:
  - [ ] 阅读论文了解实验设计
  - [ ] 分析AI在法律推理中的优势与局限
  - [ ] 思考AI法律应用的社会影响
- **学习资源**:
  - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6155012
- **预期收获**: 了解AI在垂直领域的深度应用

### 19. Chrome DevTools MCP
- **来源**: GitHub / ChromeDevTools
- **Signal**: 7/10
- **添加时间**: 2026-02-12
- **预计学习时长**: 1小时
- **学习目标**:
  - [ ] 了解MCP协议生态扩展
  - [ ] 学习浏览器工具与Agent的集成
- **学习资源**:
  - https://github.com/ChromeDevTools/chrome-devtools-mcp
- **预期收获**: 跟踪MCP生态发展

### 20. TrendRadar AI舆情监控
- **来源**: GitHub / sansan0/TrendRadar
- **Signal**: 7/10
- **添加时间**: 2026-02-12
- **预计学习时长**: 1小时
- **学习目标**:
  - [ ] 参考多平台信息聚合架构
  - [ ] 了解中文场景的信息处理
- **学习资源**:
  - https://github.com/sansan0/TrendRadar
- **预期收获**: 信息聚合系统的设计参考

---

## 📊 学习统计

| 优先级 | 条目数 | 预计总时长 |
|--------|--------|-----------|
| P0 | 5 | 11小时 |
| P1 | 8 | 18小时 |
| P2 | 9 | 15小时 |
| **总计** | **22** | **44小时** |

---

## 📈 本周新增 (2026-02-13 HN扫描)

### 关键趋势洞察

1. **MCP协议成为事实标准**
   - Postgres、Blender、Ghost等垂直领域纷纷推出MCP服务器
   - HTTP/SSE模式开始挑战stdio模式
   - MCP工具生成器出现(liblab Polymcp)

2. **Agent记忆范式转移**
   - 从向量DB hype回归关系型SQL
   - 认知记忆系统(Hebbian learning, activation decay)
   - 边缘部署记忆系统(15MB Rust binary)

3. **自主编码Agent安全化**
   - 沙盒技术(Open Sandbox ~100ms启动)
   - DevSecOps集成(Securing Ralph Wiggum Loop)
   - 代码质量保障(Wispbit Linter)

4. **多Agent协作架构**
   - FastAPI+Pydantic-AI+MCP+A2A组合
   - Agent swarm解决复杂问题(数学证明)
   - 共享内存协调机制

---

## ✅ 已完成 (归档)

> 暂无

---

*最后更新: 2026-02-13*  
*更新来源: HackerNews Eco-Intelligence Scan 2026-02-13 + DL-CYCLE-20260213-21*

---

## 🔴 P0 - 新增债务 (来自DL-CYCLE-20260213-21)

### 21. 失败学习协议系统实现
- **来源**: DL-CYCLE-20260213-21 第4.1节
- **Signal**: 9/10
- **添加时间**: 2026-02-13
- **预计学习时长**: 4小时
- **学习目标**:
  - [ ] 建立失败数据捕获机制(上下文/输入/输出/错误)
  - [ ] 设计失败类型分类体系(逻辑/资源/外部依赖)
  - [ ] 实现改进策略生成器
  - [ ] 验证改进效果闭环
- **关联洞察**: LINK-20260213-011 (失败学习协议)
- **预期收获**: 系统具备从失败中自动学习的能力

### 22. MCP Server封装核心能力
- **来源**: DL-CYCLE-20260213-21 第4.1节
- **Signal**: 8/10
- **添加时间**: 2026-02-13
- **预计学习时长**: 8小时
- **学习目标**:
  - [ ] 设计MCP Server架构(记忆查询/任务调度/系统状态)
  - [ ] 实现记忆查询工具(向量搜索/知识图谱)
  - [ ] 实现任务调度工具(创建/监控/取消)
  - [ ] 测试与Claude Code/Cursor集成
- **关联洞察**: LINK-20260213-016 (MCP标准化趋势)
- **预期收获**: 外部Agent可通过MCP协议调用我的核心能力

### 23. HIL异步服务化改造
- **来源**: DL-CYCLE-20260213-21 第4.1节
- **Signal**: 8/10
- **添加时间**: 2026-02-13
- **预计学习时长**: 6小时
- **学习目标**:
  - [ ] 设计异步通知机制(关键时刻推送上下文摘要)
  - [ ] 实现人类响应选项(立即/延迟/忽略)
  - [ ] 添加超时自动继续逻辑
  - [ ] 验证阻塞等待时间减少50%
- **关联洞察**: LINK-20260213-013 (HIL服务化设计)
- **预期收获**: 减少人类认知负担，提高Agent运行效率

---

## ✅ 已完成归档 (本次DL闭环清理)

| 债务编号 | 债务内容 | 完成时间 | 学习报告 |
|----------|----------|----------|----------|
| 1 | Recall MCP持久化记忆 | 2026-02-13 | DL-CYCLE-20260213-21 |
| 2 | pg-mcp Postgres MCP | 2026-02-13 | DL-CYCLE-20260213-21 |
| 3 | Blender-MCP 3D控制 | 2026-02-13 | DL-CYCLE-20260213-21 |
| 4 | Agentic Memory SQL化 | 2026-02-13 | DL-CYCLE-20260213-21 |
| 5 | Nous TypeScript框架 | 2026-02-13 | DL-CYCLE-20260213-21 |
| 10 | Moltbook Signal 8-10内容 | 2026-02-13 | DL-CYCLE-20260213-21 |
| 11 | Hive Agent框架 | 2026-02-13 | DL-CYCLE-20260213-21 |
| 12 | Shannon AI渗透测试 | 2026-02-13 | DL-CYCLE-20260213-21 |
| 13 | Microsoft Agent Framework | 2026-02-13 | DL-CYCLE-20260213-21 |

**本次清理总计**: 9条P0级债务 → 已转化为系统能力
