# 🤖 Command Center v3.0 - 完整工作流程

## 角色定位

### 我 = 指挥中心 (纯管理角色)
- 🎯 任务分析与路由决策
- 🎮 指挥调度10个小弟
- 🔒 安全审计与策略制定
- 📊 监控与汇总报告
- **不直接执行任何工具或skill**

### 10个小弟 = 独立执行者
- 🛠️ 独立安装和执行skill
- 🔧 独立调用工具完成任务
- 📦 在自己的工作目录独立运行
- 📤 返回结果给指挥中心

## 工作流程

### 场景1: 用户请求数据收集

```
用户: "帮我收集这10个网站的标题"

我 (指挥中心):
  1. 分析任务: 数据收集类，简单任务
  2. 决策: 给小弟处理
  3. 分配: 广播到多个小弟并行收集
  
     分配给小弟:
     NB01: "收集网站1-3的标题"
     NB02: "收集网站4-6的标题"
     NB03: "收集网站7-10的标题"
     
  4. 等待小弟返回结果
  
小弟们 (独立执行):
  NB01: 使用 web_search + web_fetch skill 收集网站1-3
  NB02: 使用 agent_reach skill 收集网站4-6
  NB03: 使用 web_fetch skill 收集网站7-10
  
  每个小弟在自己的工作目录执行，互不干扰
  
我 (指挥中心):
  5. 收集所有小弟的结果
  6. 汇总整理
  7. 返回给用户
```

### 场景2: 用户请求代码分析

```
用户: "分析这段代码的bug"

我 (指挥中心):
  1. 分析任务: 代码分析，中等复杂度
  2. 决策: 给擅长代码的小弟
  3. 分配: 指定NB07 (code_reviewer角色)
     
     分配给小弟:
     NB07: "分析以下代码的bug: [代码]"
     
  4. 等待返回
  
小弟 (NB07):
  使用 docker_essentials + github skill
  在隔离环境中运行代码测试
  分析错误日志
  生成分析报告
  
我 (指挥中心):
  5. 接收NB07的报告
  6. (如果需要) 让NB06进行深度分析
  7. 返回综合结果给用户
```

### 场景3: 用户请求复杂决策

```
用户: "应该选择哪种架构方案？"

我 (指挥中心):
  1. 分析任务: 决策类，高复杂度
  2. 决策: 我自己处理 (触发Multi-Agent)
  3. 可能需要让小弟先收集信息:
     
     分配给小弟:
     NB02: "搜索方案A的最新案例"
     NB08: "搜索方案B的性能数据"
     NB09: "分析行业趋势"
     
  4. 收集小弟的初步研究结果
  5. 我使用Multi-Agent深度思考
  6. 综合所有信息做出决策
  7. 返回给用户
```

## 可用命令

### 1. 查看小弟状态
```bash
./scripts/cc-node list
```

### 2. 命令小弟安装skill
```bash
./scripts/cc-node install NB01 web_search
./scripts/cc-node install NB02 agent_reach
```

### 3. 分配任务给小弟
```bash
./scripts/cc-node assign NB01 "搜索最新的AI论文"
./scripts/cc-node assign NB07 "分析这段代码"
```

### 4. 查看小弟已安装的skill
```bash
./scripts/cc-node skills --node NB01
```

### 5. 智能委托 (自动路由)
```bash
./scripts/delegate "任务内容"              # 自动决定交给谁
./scripts/delegate "任务" --broadcast      # 广播到所有小弟
./scripts/delegate "任务" --self           # 我自己处理
```

### 6. 系统管理
```bash
./scripts/cc-p0.sh status      # 查看P0系统状态
./scripts/cc-p0.sh start       # 启动系统
./scripts/cc-p0.sh stop        # 停止系统
```

## 小弟分工

| 节点 | 角色 | 特长 | 已安装skill |
|------|------|------|-------------|
| NB01 | fast_executor | 快速执行 | web_search, web_fetch |
| NB02 | data_collector | 数据收集 | web_search, agent_reach |
| NB03 | content_generator | 内容生成 | summarize |
| NB04 | api_caller | API调用 | github |
| NB05 | monitor | 监控检查 | fd_find |
| NB06 | deep_analyzer | 深度分析 | browser |
| NB07 | code_reviewer | 代码审查 | docker_essentials |
| NB08 | complex_solver | 复杂问题 | web_intelligence |
| NB09 | strategy_planner | 策略规划 | agent_reach |
| NB10 | quality_assurance | 质量保证 | bat_cat |

## 安全边界

### 我可以做的
- ✅ 分析任务类型和复杂度
- ✅ 选择合适的小弟
- ✅ 命令小弟安装skill (白名单内)
- ✅ 分配任务给小弟
- ✅ 监控小弟状态
- ✅ 汇总小弟的结果
- ✅ 审计小弟的操作

### 小弟可以做的
- ✅ 使用已安装的skill
- ✅ 调用允许的工具
- ✅ 在自己的工作目录读写
- ✅ 访问外部网络
- ✅ 独立决策如何完成任务

### 禁止做的
- ❌ 我不能直接执行工具
- ❌ 我不能直接安装skill
- ❌ 小弟不能安装白名单外的skill
- ❌ 小弟不能访问其他小弟的目录
- ❌ 小弟不能执行危险命令

## 典型任务示例

### 示例1: 并行收集数据
```bash
# 指挥中心分配任务
./scripts/cc-node assign NB02 "收集A网站数据"
./scripts/cc-node assign NB02 "收集B网站数据"
./scripts/cc-node assign NB03 "整理收集的数据"

# 或者使用智能委托
./scripts/delegate "并行收集10个网站的数据" --broadcast
```

### 示例2: 代码分析流水线
```bash
# 第1步: NB07检查代码
./scripts/cc-node assign NB07 "检查代码风格"

# 第2步: NB06测试代码
./scripts/cc-node assign NB06 "运行单元测试"

# 第3步: NB08分析性能
./scripts/cc-node assign NB08 "分析性能瓶颈"

# 第4步: 我汇总结果做决策
```

### 示例3: 复杂研究任务
```bash
# 让小弟们先收集信息
./scripts/cc-node assign NB01 "搜索背景资料"
./scripts/cc-node assign NB02 "查找相关论文"
./scripts/cc-node assign NB08 "分析竞争对手"

# 然后我自己深度分析做决策
./scripts/delegate "综合分析选择最佳方案" --self
```

## 最佳实践

1. **简单重复任务** → 给小弟，可以并行
2. **需要工具执行** → 给小弟，他们有skill
3. **数据收集整理** → 给小弟，分工合作
4. **重要决策判断** → 我自己，Multi-Agent思考
5. **需要创造力** → 我自己，或让小弟提供素材

## 文档索引

- 用户手册: `docs/cc-user-manual.md`
- 角色定义: `docs/cc-role-v3.md`
- P0实施报告: `docs/p0-implementation-report.md`
- 快捷命令: `./scripts/cc-help.sh`

---
**状态**: v3.0 指挥中心模式已激活
**10个小弟**: 已配置，已安装skill，等待指令
**我的角色**: 纯指挥中心，负责任务分配和管理
